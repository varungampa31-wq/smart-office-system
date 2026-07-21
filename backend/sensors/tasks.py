"""
Background processing for sensor readings.

The ingestion view (sensors/views.py: SensorIngestView) never writes to
the database itself -- it validates the request came from a trusted fog
node, then calls process_sensor_reading.delay(payload) for every reading
in the batch and returns immediately. This task is what actually runs
(on one or more separate `celery worker` processes) and does the real
work: resolve the employee if the reading references one, apply simple
threshold rules, and persist the SensorEvent (and an Alert, if needed).

Why this matters for the "scalable backend" requirement: the ingestion
endpoint's response time no longer depends on DB write latency or on how
many employees/alerts logic has to look up, and worker processes can be
scaled horizontally/independently of the web process as sensor volume
grows.
"""
from django.conf import settings
from django.utils.dateparse import parse_datetime

from celery import shared_task

from employees.models import Employee
from sensors.models import SensorEvent
from alerts.models import Alert


def _resolve_employee(payload: dict):
    """Best-effort employee lookup from an RFID tag or employee_id in the
    payload. Returns None (not an error) if not present/found -- most
    ambient sensor readings (temperature, occupancy) have no employee."""
    rfid_tag = payload.get("rfid_tag")
    employee_id = payload.get("employee_id")

    if rfid_tag:
        return Employee.objects.filter(rfid_tag=rfid_tag).first()
    if employee_id:
        return Employee.objects.filter(employee_id=employee_id).first()
    return None


def _maybe_raise_alert(payload: dict, employee, event: SensorEvent):
    """Very small rule engine applied at ingestion time. Extend this for
    the report if you want to discuss "edge/cloud analytics" -- in a
    bigger system this logic (or a cheaper version of it) would run on
    the fog node itself to cut cloud round-trips."""
    sensor_type = payload.get("sensor_type")
    value = payload.get("value")

    if sensor_type == "TEMPERATURE" and value is not None:
        if value >= settings.TEMPERATURE_ALERT_MAX_C:
            Alert.objects.create(
                employee=employee,
                alert_type="SENSOR_THRESHOLD",
                severity="HIGH",
                description=(
                    f"Temperature sensor {payload.get('device_id')} reported "
                    f"{value}{payload.get('unit', 'C')}, above the "
                    f"{settings.TEMPERATURE_ALERT_MAX_C} threshold."
                ),
            )
            event.event_type = "THRESHOLD_EXCEEDED"
            event.save(update_fields=["event_type"])

    if sensor_type == "HUMIDITY" and value is not None:
        if value >= settings.HUMIDITY_ALERT_MAX_PCT:
            Alert.objects.create(
                employee=employee,
                alert_type="SENSOR_THRESHOLD",
                severity="MEDIUM",
                description=(
                    f"Humidity sensor {payload.get('device_id')} reported "
                    f"{value}{payload.get('unit', '%')}, above the "
                    f"{settings.HUMIDITY_ALERT_MAX_PCT} threshold."
                ),
            )
            event.event_type = "THRESHOLD_EXCEEDED"
            event.save(update_fields=["event_type"])

    if sensor_type == "RFID" and payload.get("event_type") == "INVALID_RFID":
        Alert.objects.create(
            employee=None,
            alert_type="INVALID_RFID",
            severity="HIGH",
            description=f"Unknown RFID scanned: {payload.get('rfid_tag', 'unknown')}",
        )


@shared_task(name="sensors.process_sensor_reading")
def process_sensor_reading(payload: dict):
    """
    Expected payload shape (see fog_node/schemas.py for the pydantic
    version the fog node validates against before it ever gets here):

    {
        "sensor_type": "TEMPERATURE" | "HUMIDITY" | "OCCUPANCY" | "DOOR" | "RFID",
        "event_type": "READING" | "RFID_SCAN" | "INVALID_RFID" | "DOOR_OPEN" | ...,
        "device_id": "TEMP_SENSOR_01",
        "value": 23.4,                # optional, ambient sensors
        "unit": "C",                  # optional
        "rfid_tag": "AB12CD34",       # optional, identity sensors
        "employee_id": "EMP001",      # optional, alternative to rfid_tag
        "recorded_at": "2026-07-20T10:15:00Z",  # when the sensor captured it
        "fog_node_id": "fog-01",
        "raw": { ... }                # anything else, stored as-is
    }
    """
    employee = _resolve_employee(payload)

    recorded_at = payload.get("recorded_at")
    recorded_at_dt = parse_datetime(recorded_at) if recorded_at else None

    event = SensorEvent.objects.create(
        employee=employee,
        sensor_type=payload.get("sensor_type", "RFID"),
        event_type=payload.get("event_type", "READING"),
        device_id=payload.get("device_id", "UNKNOWN"),
        value=payload.get("value"),
        unit=payload.get("unit"),
        fog_node_id=payload.get("fog_node_id"),
        recorded_at=recorded_at_dt,
        processed=True,
        raw_data=payload.get("raw"),
    )

    _maybe_raise_alert(payload, employee, event)

    return event.id
