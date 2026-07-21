from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "department",
        "email",
        "is_active",
        "created_at",
    )

    search_fields = (
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "rfid_tag",
    )

    list_filter = (
        "department",
        "is_active",
    )

    ordering = (
        "employee_id",
    )