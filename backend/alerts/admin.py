from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "alert_type",
        "employee",
        "severity",
        "resolved",
        "timestamp",
    )

    list_filter = (
        "severity",
        "resolved",
        "alert_type",
    )

    search_fields = (
        "employee__employee_id",
        "description",
    )

    ordering = (
        "-timestamp",
    )