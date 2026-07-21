from django.db import models
from employees.models import Employee


class SensorEvent(models.Model):
    # NOTE: Original choices only covered identity/access sensors (RFID,
    # fingerprint, face, door, exit). Extended with ambient/environmental
    # sensor types so the fog layer can report readings that are not tied
    # to a specific employee (temperature, humidity, occupancy count, etc).
    SENSOR_CHOICES = [
        ("RFID", "RFID"),
        ("FINGERPRINT", "Fingerprint"),
        ("FACE", "Face Recognition"),
        ("DOOR", "Door Sensor"),
        ("EXIT", "Exit Sensor"),
        ("TEMPERATURE", "Temperature Sensor"),
        ("HUMIDITY", "Humidity Sensor"),
        ("OCCUPANCY", "Occupancy / Motion Sensor"),
        ("CAMERA", "Camera / Face Verification"),
    ]

    EVENT_CHOICES = [
        ("CHECK_IN", "Check In"),
        ("CHECK_OUT", "Check Out"),
        ("ACCESS_GRANTED", "Access Granted"),
        ("ACCESS_DENIED", "Access Denied"),
        ("RFID_SCAN", "RFID Scan"),
        ("INVALID_RFID", "Invalid RFID"),
        ("DOOR_OPEN", "Door Open"),
        ("DOOR_CLOSED", "Door Closed"),
        ("ENTRY_DETECTED", "Entry Detected"),
        ("EXIT_DETECTED", "Exit Detected"),
        ("READING", "Ambient Reading"),
        ("THRESHOLD_EXCEEDED", "Threshold Exceeded"),
        ("FACE_VERIFIED", "Face Verified"),
    ]

    # Ambient/environmental sensor readings (temperature, humidity, an
    # occupancy sensor covering a whole room, etc.) are not necessarily
    # tied to one employee, so this must be nullable. It was previously
    # a required FK, which meant any event without a resolved employee
    # (e.g. an invalid RFID scan) would fail at the database level.
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="sensor_events",
        null=True,
        blank=True,
    )

    sensor_type = models.CharField(
        max_length=20,
        choices=SENSOR_CHOICES
    )

    event_type = models.CharField(
        max_length=30,
        choices=EVENT_CHOICES
    )

    device_id = models.CharField(
        max_length=50
    )

    # Numeric payload for ambient sensors (e.g. 21.6 for a temperature
    # reading in Celsius, 1 for occupancy detected). Identity/access
    # sensors can leave this blank and rely on event_type instead.
    value = models.FloatField(
        blank=True,
        null=True,
    )

    unit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    # Which fog node forwarded this reading, useful once you run more
    # than one fog node / for tracing in the report.
    fog_node_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    # When the sensor itself captured the reading (set by the fog node).
    # `timestamp` below records when the backend stored it, so the gap
    # between the two is the sensor -> fog -> cloud latency.
    recorded_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    processed = models.BooleanField(
        default=False
    )

    raw_data = models.JSONField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Sensor Event"
        verbose_name_plural = "Sensor Events"

    def __str__(self):
        who = self.employee.employee_id if self.employee else "N/A"
        return f"{who} - {self.sensor_type}"