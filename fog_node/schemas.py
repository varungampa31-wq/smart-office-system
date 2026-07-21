from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


VALID_SENSOR_TYPES = {
    "RFID",
    "FINGERPRINT",
    "FACE",
    "DOOR",
    "EXIT",
    "TEMPERATURE",
    "HUMIDITY",
    "OCCUPANCY",
    "CAMERA",
}


class SensorReading(BaseModel):
    """
    What a sensor simulator POSTs to the fog node. Kept intentionally
    close to what the Django backend eventually stores (sensors.models.
    SensorEvent) but the fog node is the one place allowed to add
    fog-only fields (fog_node_id, received_at) before forwarding.
    """
    sensor_type: str
    event_type: str = "READING"
    device_id: str
    value: Optional[float] = None
    unit: Optional[str] = None
    rfid_tag: Optional[str] = None
    employee_id: Optional[str] = None
    recorded_at: Optional[datetime] = None
    raw: Optional[dict[str, Any]] = None

    def with_defaults(self) -> dict:
        data = self.model_dump()
        if not data.get("recorded_at"):
            data["recorded_at"] = datetime.now(timezone.utc).isoformat()
        else:
            # normalise to isoformat string for JSON transport
            data["recorded_at"] = self.recorded_at.isoformat()
        return data
