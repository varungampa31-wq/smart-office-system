import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Identity of this fog node instance -- stored on every SensorEvent it
    # forwards (sensors.fog_node_id). Run several fog nodes with different
    # IDs if you want to demo multiple "virtual" edge locations.
    FOG_NODE_ID = os.environ.get("FOG_NODE_ID", "fog-01")

    # Where the fog node listens for readings pushed by the sensor
    # simulators.
    HOST = os.environ.get("FOG_HOST", "0.0.0.0")
    PORT = int(os.environ.get("FOG_PORT", "9000"))

    # The Django backend's ingestion endpoint + shared API key. Must match
    # FOG_INGEST_API_KEY in backend/.env.
    BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
    BACKEND_INGEST_PATH = "/api/sensors/ingest/"
    FOG_INGEST_API_KEY = os.environ.get("FOG_INGEST_API_KEY", "dev-fog-api-key-change-me")

    # How often the fog node flushes its local buffer to the cloud
    # backend, in seconds. This is the "configurable dispatch rate" the
    # brief asks for -- lower it for a livelier demo, raise it to show
    # batching/backpressure behaviour in the report.
    DISPATCH_INTERVAL_SECONDS = float(os.environ.get("DISPATCH_INTERVAL_SECONDS", "5"))

    # Safety cap so one dispatch call can't try to send an unbounded
    # batch if the backend has been unreachable for a while.
    MAX_BATCH_SIZE = int(os.environ.get("FOG_MAX_BATCH_SIZE", "200"))

    # Simple local (edge) filtering: temperature readings within this many
    # degrees of the previous reading for the same device are considered
    # noise and are still stored but flagged, not something we'd escalate.
    # Demonstrates "fog node processes data" beyond pure pass-through.
    TEMPERATURE_NOISE_BAND_C = float(os.environ.get("TEMPERATURE_NOISE_BAND_C", "0.2"))

    HTTP_TIMEOUT_SECONDS = float(os.environ.get("FOG_HTTP_TIMEOUT_SECONDS", "5"))
    HTTP_RETRY_ATTEMPTS = int(os.environ.get("FOG_HTTP_RETRY_ATTEMPTS", "3"))


settings = Settings()
