import os

from dotenv import load_dotenv

load_dotenv()


def _float_env(name: str, default: str) -> float:
    return float(os.environ.get(name, default))


class Settings:
    # Where the fog node listens (see fog_node/main.py). docker-compose:
    # use the service name, e.g. http://fog_node:9000
    FOG_NODE_URL = os.environ.get("FOG_NODE_URL", "http://localhost:9000")

    HTTP_TIMEOUT_SECONDS = _float_env("SIM_HTTP_TIMEOUT_SECONDS", "5")

    # --- Per-sensor frequency (seconds between readings) ---------------
    # This is the "configurable frequency" the brief asks for. Each of
    # the 5 sensor types runs its own independent loop, so they don't
    # have to share a rate.
    RFID_INTERVAL_SECONDS = _float_env("RFID_INTERVAL_SECONDS", "8")
    TEMPERATURE_INTERVAL_SECONDS = _float_env("TEMPERATURE_INTERVAL_SECONDS", "4")
    HUMIDITY_INTERVAL_SECONDS = _float_env("HUMIDITY_INTERVAL_SECONDS", "6")
    OCCUPANCY_INTERVAL_SECONDS = _float_env("OCCUPANCY_INTERVAL_SECONDS", "5")
    DOOR_INTERVAL_SECONDS = _float_env("DOOR_INTERVAL_SECONDS", "10")

    # RFID tags known to the seeded demo employees (see backend
    # employees/management/commands/seed_demo.py). Override via env as a
    # comma-separated list if you seed different employees.
    KNOWN_RFID_TAGS = os.environ.get(
        "KNOWN_RFID_TAGS",
        "RFID-A1001,RFID-A1002,RFID-A1003,RFID-A1004,RFID-A1005",
    ).split(",")

    # Chance (0-1) that an RFID scan uses an unrecognised tag, to exercise
    # the INVALID_RFID / alert path.
    INVALID_RFID_PROBABILITY = _float_env("INVALID_RFID_PROBABILITY", "0.15")

    # Ambient sensor baselines + drift, tuned so TEMPERATURE_ALERT_MAX_C
    # (default 30 in backend settings) gets crossed occasionally but not
    # constantly -- gives you something to point at in a demo/report
    # without every reading being an alert.
    TEMPERATURE_BASELINE_C = _float_env("TEMPERATURE_BASELINE_C", "22.0")
    TEMPERATURE_SPIKE_PROBABILITY = _float_env("TEMPERATURE_SPIKE_PROBABILITY", "0.1")

    HUMIDITY_BASELINE_PCT = _float_env("HUMIDITY_BASELINE_PCT", "45.0")
    HUMIDITY_SPIKE_PROBABILITY = _float_env("HUMIDITY_SPIKE_PROBABILITY", "0.1")

    DEVICE_ID_SUFFIX = os.environ.get("SIM_DEVICE_SUFFIX", "01")


settings = Settings()
