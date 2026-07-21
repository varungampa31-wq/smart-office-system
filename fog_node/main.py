"""
Virtual fog node.

Role in the architecture (see docs/ARCHITECTURE.md for the full picture):

    sensor simulators  --HTTP-->  THIS SERVICE (fog node)  --HTTP batch-->  Django backend (queue -> DB)

Sensors POST individual readings to /ingest/{sensor_type} as they're
generated. The fog node does NOT forward each reading immediately.
Instead it:

  1. Buffers readings in memory.
  2. Applies light "edge processing" (tags with fog_node_id + received_at,
     flags temperature/humidity readings that barely moved since the last
     reading from the same device as noise) -- this is the fog layer's
     actual contribution, not just a proxy.
  3. On a fixed interval (DISPATCH_INTERVAL_SECONDS, configurable), flushes
     the buffer to the backend's /api/sensors/ingest/ endpoint as one
     batch, which keeps request volume against the cloud backend low and
     predictable regardless of how chatty the sensors are.

Run standalone with:
    uvicorn fog_node.main:app --host 0.0.0.0 --port 9000
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException

from .config import settings
from .schemas import SensorReading, VALID_SENSOR_TYPES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [fog:%(name)s] %(message)s")
logger = logging.getLogger(settings.FOG_NODE_ID)


class FogState:
    """In-memory buffer + running counters. A single fog node process is
    assumed here (no shared state needed); if you wanted multiple fog
    node replicas behind a load balancer you'd move this buffer to Redis
    the same way the backend uses it for Celery."""

    def __init__(self):
        self.buffer: list[dict] = []
        self.lock = asyncio.Lock()
        self.last_value_by_device: dict[str, float] = {}
        self.received_total = 0
        self.dispatched_total = 0
        self.dispatch_failures = 0
        self.flagged_noise_total = 0
        self.last_dispatch_at: datetime | None = None
        self.last_dispatch_error: str | None = None


state = FogState()


def _apply_edge_processing(reading: dict) -> dict:
    """Tiny bit of local intelligence so the fog node is doing more than
    passing bytes through. Extend this for the report if you want to
    argue for more fog-side analytics (e.g. rolling averages, dedup)."""
    reading["fog_node_id"] = settings.FOG_NODE_ID

    if reading["sensor_type"] in ("TEMPERATURE", "HUMIDITY") and reading.get("value") is not None:
        device_id = reading["device_id"]
        previous = state.last_value_by_device.get(device_id)
        state.last_value_by_device[device_id] = reading["value"]

        if previous is not None and abs(reading["value"] - previous) <= settings.TEMPERATURE_NOISE_BAND_C:
            if reading.get("raw") is None:
                reading["raw"] = {}
            reading["raw"]["fog_flag"] = "within_noise_band"
            state.flagged_noise_total += 1

    return reading


async def _dispatch_loop():
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        while True:
            await asyncio.sleep(settings.DISPATCH_INTERVAL_SECONDS)
            await _flush(client)


async def _flush(client: httpx.AsyncClient):
    async with state.lock:
        if not state.buffer:
            return
        batch, state.buffer = state.buffer[: settings.MAX_BATCH_SIZE], state.buffer[settings.MAX_BATCH_SIZE :]

    url = settings.BACKEND_URL.rstrip("/") + settings.BACKEND_INGEST_PATH
    headers = {"X-API-Key": settings.FOG_INGEST_API_KEY}

    attempt = 0
    while attempt < settings.HTTP_RETRY_ATTEMPTS:
        attempt += 1
        try:
            resp = await client.post(url, json={"readings": batch}, headers=headers)
            resp.raise_for_status()
            state.dispatched_total += len(batch)
            state.last_dispatch_at = datetime.now(timezone.utc)
            state.last_dispatch_error = None
            logger.info("Dispatched %d reading(s) to backend (%s)", len(batch), resp.status_code)
            return
        except (httpx.HTTPError, httpx.HTTPStatusError) as exc:
            state.last_dispatch_error = str(exc)
            logger.warning("Dispatch attempt %d/%d failed: %s", attempt, settings.HTTP_RETRY_ATTEMPTS, exc)
            await asyncio.sleep(min(2 ** attempt, 10))

    # All retries exhausted -- put the batch back at the front of the
    # buffer so nothing is silently dropped, and count the failure.
    state.dispatch_failures += 1
    async with state.lock:
        state.buffer = batch + state.buffer
    logger.error("Giving up on batch of %d reading(s) after %d attempts; re-buffered.", len(batch), settings.HTTP_RETRY_ATTEMPTS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_dispatch_loop())
    logger.info(
        "Fog node '%s' started. Dispatching to %s every %ss.",
        settings.FOG_NODE_ID, settings.BACKEND_URL, settings.DISPATCH_INTERVAL_SECONDS,
    )
    yield
    task.cancel()


app = FastAPI(title="Smart Office Fog Node", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "fog_node_id": settings.FOG_NODE_ID}


@app.get("/stats")
async def stats():
    async with state.lock:
        buffer_size = len(state.buffer)
    return {
        "fog_node_id": settings.FOG_NODE_ID,
        "buffer_size": buffer_size,
        "received_total": state.received_total,
        "dispatched_total": state.dispatched_total,
        "dispatch_failures": state.dispatch_failures,
        "flagged_noise_total": state.flagged_noise_total,
        "last_dispatch_at": state.last_dispatch_at,
        "last_dispatch_error": state.last_dispatch_error,
        "dispatch_interval_seconds": settings.DISPATCH_INTERVAL_SECONDS,
        "backend_url": settings.BACKEND_URL,
    }


@app.post("/ingest/{sensor_type}")
async def ingest(sensor_type: str, reading: SensorReading):
    sensor_type = sensor_type.upper()
    if sensor_type not in VALID_SENSOR_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown sensor_type '{sensor_type}'")
    if reading.sensor_type.upper() != sensor_type:
        raise HTTPException(status_code=400, detail="sensor_type in body must match the URL path")

    payload = _apply_edge_processing(reading.with_defaults())

    async with state.lock:
        state.buffer.append(payload)
        state.received_total += 1

    return {"status": "buffered", "buffer_size": len(state.buffer)}