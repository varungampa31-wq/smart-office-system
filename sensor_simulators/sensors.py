"""
Five independent sensor simulators, each an async loop that generates a
reading on its own schedule and hands it to a dispatch callback (which
posts it to the fog node -- see dispatcher.py). Modelling them as
separate classes/loops (rather than one generic "random sensor") mirrors
real fog/edge setups where different physical sensors have different
sampling rates and payload shapes.
"""
import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from .config import settings

logger = logging.getLogger("sensor_simulators")

DispatchFn = Callable[[str, dict], Awaitable[None]]


class BaseSensor(ABC):
    sensor_type: str
    interval_seconds: float
    device_id: str

    def __init__(self, dispatch: DispatchFn):
        self.dispatch = dispatch

    @abstractmethod
    def generate_reading(self) -> dict:
        """Return a payload matching fog_node.schemas.SensorReading."""
        raise NotImplementedError

    async def run(self):
        logger.info("%s starting (every %ss)", self.sensor_type, self.interval_seconds)
        while True:
            reading = self.generate_reading()
            try:
                await self.dispatch(self.sensor_type.lower(), reading)
                logger.info("%s -> %s", self.sensor_type, {k: v for k, v in reading.items() if k != "raw"})
            except Exception as exc:  # noqa: BLE001 - a single failed send shouldn't kill the loop
                logger.warning("%s: failed to dispatch reading: %s", self.sensor_type, exc)
            await asyncio.sleep(self.interval_seconds)


class RFIDBadgeSensor(BaseSensor):
    """Simulates an RFID reader at the front door. Mostly scans known
    employee badges, occasionally an unrecognised one to exercise the
    INVALID_RFID / alerting path end-to-end."""
    sensor_type = "RFID"
    interval_seconds = settings.RFID_INTERVAL_SECONDS
    device_id = f"RFID_SIM_{settings.DEVICE_ID_SUFFIX}"

    def generate_reading(self) -> dict:
        if random.random() < settings.INVALID_RFID_PROBABILITY or not settings.KNOWN_RFID_TAGS:
            tag = f"RFID-UNKNOWN-{random.randint(1000, 9999)}"
            return {
                "sensor_type": self.sensor_type,
                "event_type": "INVALID_RFID",
                "device_id": self.device_id,
                "rfid_tag": tag,
                "raw": {"scanned_tag": tag},
            }

        tag = random.choice(settings.KNOWN_RFID_TAGS)
        return {
            "sensor_type": self.sensor_type,
            "event_type": "RFID_SCAN",
            "device_id": self.device_id,
            "rfid_tag": tag,
        }


class TemperatureSensor(BaseSensor):
    """Random-walk temperature reading around a baseline, with an
    occasional spike so the backend's threshold-alert logic has
    something to fire on during a demo."""
    sensor_type = "TEMPERATURE"
    interval_seconds = settings.TEMPERATURE_INTERVAL_SECONDS
    device_id = f"TEMP_SIM_{settings.DEVICE_ID_SUFFIX}"

    def __init__(self, dispatch: DispatchFn):
        super().__init__(dispatch)
        self._current = settings.TEMPERATURE_BASELINE_C

    def generate_reading(self) -> dict:
        if random.random() < settings.TEMPERATURE_SPIKE_PROBABILITY:
            self._current = settings.TEMPERATURE_BASELINE_C + random.uniform(8, 14)
        else:
            self._current += random.uniform(-0.6, 0.6)
            # drift back toward baseline so it doesn't wander forever
            self._current += (settings.TEMPERATURE_BASELINE_C - self._current) * 0.1

        return {
            "sensor_type": self.sensor_type,
            "event_type": "READING",
            "device_id": self.device_id,
            "value": round(self._current, 1),
            "unit": "C",
        }


class HumiditySensor(BaseSensor):
    sensor_type = "HUMIDITY"
    interval_seconds = settings.HUMIDITY_INTERVAL_SECONDS
    device_id = f"HUMIDITY_SIM_{settings.DEVICE_ID_SUFFIX}"

    def __init__(self, dispatch: DispatchFn):
        super().__init__(dispatch)
        self._current = settings.HUMIDITY_BASELINE_PCT

    def generate_reading(self) -> dict:
        if random.random() < settings.HUMIDITY_SPIKE_PROBABILITY:
            self._current = settings.HUMIDITY_BASELINE_PCT + random.uniform(20, 35)
        else:
            self._current += random.uniform(-2, 2)
            self._current += (settings.HUMIDITY_BASELINE_PCT - self._current) * 0.1

        self._current = max(0, min(100, self._current))

        return {
            "sensor_type": self.sensor_type,
            "event_type": "READING",
            "device_id": self.device_id,
            "value": round(self._current, 1),
            "unit": "%",
        }


class OccupancyMotionSensor(BaseSensor):
    """Toggles between entry/exit detected, loosely modelling a PIR
    motion sensor at a room entrance."""
    sensor_type = "OCCUPANCY"
    interval_seconds = settings.OCCUPANCY_INTERVAL_SECONDS
    device_id = f"OCC_SIM_{settings.DEVICE_ID_SUFFIX}"

    def __init__(self, dispatch: DispatchFn):
        super().__init__(dispatch)
        self._occupied = False

    def generate_reading(self) -> dict:
        self._occupied = not self._occupied if random.random() < 0.7 else self._occupied
        event_type = "ENTRY_DETECTED" if self._occupied else "EXIT_DETECTED"
        return {
            "sensor_type": self.sensor_type,
            "event_type": event_type,
            "device_id": self.device_id,
            "value": 1 if self._occupied else 0,
        }


class DoorContactSensor(BaseSensor):
    """Models a magnetic door contact sensor: open/closed state."""
    sensor_type = "DOOR"
    interval_seconds = settings.DOOR_INTERVAL_SECONDS
    device_id = f"DOOR_SIM_{settings.DEVICE_ID_SUFFIX}"

    def __init__(self, dispatch: DispatchFn):
        super().__init__(dispatch)
        self._open = False

    def generate_reading(self) -> dict:
        self._open = not self._open
        event_type = "DOOR_OPEN" if self._open else "DOOR_CLOSED"
        return {
            "sensor_type": self.sensor_type,
            "event_type": event_type,
            "device_id": self.device_id,
            "value": 1 if self._open else 0,
        }


ALL_SENSOR_CLASSES = [
    RFIDBadgeSensor,
    TemperatureSensor,
    HumiditySensor,
    OccupancyMotionSensor,
    DoorContactSensor,
]
