import logging

import httpx

from .config import settings

logger = logging.getLogger("sensor_simulators")


class FogDispatcher:
    """Thin wrapper around a shared httpx client so all sensors reuse one
    connection pool instead of opening a new connection per reading."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
        return self

    async def __aexit__(self, *exc):
        if self._client:
            await self._client.aclose()

    async def send(self, sensor_type_path: str, reading: dict):
        url = f"{settings.FOG_NODE_URL.rstrip('/')}/ingest/{sensor_type_path}"
        resp = await self._client.post(url, json=reading)
        resp.raise_for_status()
        return resp.json()
