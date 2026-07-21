from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.first_name",
        read_only=True
    )

    employee_last_name = serializers.CharField(
        source="employee.last_name",
        read_only=True
    )

    employee_id = serializers.CharField(
        source="employee.employee_id",
        read_only=True
    )

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee",
            "employee_id",
            "employee_name",
            "employee_last_name",
            "date",
            "check_in",
            "check_out",
            "working_hours",
            "status",
        ]