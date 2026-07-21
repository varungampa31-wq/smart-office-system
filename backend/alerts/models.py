from django.db import models
from employees.models import Employee


class Alert(models.Model):
    ALERT_TYPES = [
        ("UNAUTHORIZED_ACCESS", "Unauthorized Access"),
        ("INVALID_RFID", "Invalid RFID"),
        ("FINGERPRINT_FAILED", "Fingerprint Failed"),
        ("FACE_NOT_MATCHED", "Face Not Matched"),
        ("DOOR_FORCED", "Door Forced Open"),
        ("TAILGATING", "Tailgating"),
        ("MULTIPLE_SCAN", "Multiple Scan After Checkout"),
        ("SENSOR_THRESHOLD", "Ambient Sensor Threshold Exceeded"),
    ]

    SEVERITY = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="alerts",
        null=True,
        blank=True,
    )

    alert_type = models.CharField(
        max_length=50,
        choices=ALERT_TYPES,
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY,
        default="LOW",
    )

    description = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return self.alert_type