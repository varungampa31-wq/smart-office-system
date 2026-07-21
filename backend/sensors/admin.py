from django.contrib import admin
from .models import SensorEvent


@admin.register(SensorEvent)
class SensorEventAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "sensor_type",
        "event_type",
        "device_id",
        "value",
        "unit",
        "fog_node_id",
        "processed",
        "timestamp",
    )

    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
        "device_id",
        "fog_node_id",
    )

    list_filter = (
        "sensor_type",
        "event_type",
        "processed",
    )

    ordering = (
        "-timestamp",
    )
