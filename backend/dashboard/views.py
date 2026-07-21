from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from employees.models import Employee
from attendance.models import Attendance
from sensors.models import SensorEvent
from alerts.models import Alert


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        total_employees = Employee.objects.count()
        present_today = Attendance.objects.filter(date=today).count()

        employees_inside = Attendance.objects.filter(
            date=today,
            check_in__isnull=False,
            check_out__isnull=True
        ).count()

        alerts_today = Alert.objects.filter(
            timestamp__date=today
        ).count()

        sensor_events_today = SensorEvent.objects.filter(
            timestamp__date=today
        ).count()

        return Response({
            "total_employees": total_employees,
            "present_today": present_today,
            "employees_inside": employees_inside,
            "alerts_today": alerts_today,
            "sensor_events_today": sensor_events_today
        })


class LiveDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        summary = {
            "total_employees": Employee.objects.count(),
            "present_today": Attendance.objects.filter(date=today).count(),
            "employees_inside": Attendance.objects.filter(
                date=today,
                check_in__isnull=False,
                check_out__isnull=True
            ).count(),
            "alerts_today": Alert.objects.filter(
                timestamp__date=today
            ).count(),
            "sensor_events_today": SensorEvent.objects.filter(
                timestamp__date=today
            ).count(),
        }

        inside = Attendance.objects.filter(
            date=today,
            check_in__isnull=False,
            check_out__isnull=True
        )

        employees_inside = []

        for attendance in inside:
            employees_inside.append({
                "employee_id": attendance.employee.employee_id,
                "name": f"{attendance.employee.first_name} {attendance.employee.last_name}",
                "department": attendance.employee.department,
                "check_in": attendance.check_in.strftime("%H:%M:%S")
            })

        recent_events = SensorEvent.objects.order_by("-timestamp")[:10]

        sensor_events = []

        for event in recent_events:
            sensor_events.append({
                "employee": (
                    f"{event.employee.first_name} {event.employee.last_name}"
                    if event.employee else "Unknown"
                ),
                "event": event.event_type,
                "sensor": event.sensor_type,
                "time": event.timestamp.strftime("%H:%M:%S")
            })

        recent_alerts = Alert.objects.order_by("-timestamp")[:10]

        alerts = []

        for alert in recent_alerts:
            alerts.append({
                "employee": (
                    f"{alert.employee.first_name} {alert.employee.last_name}"
                    if alert.employee else "Unknown"
                ),
                "type": alert.alert_type,
                "severity": alert.severity,
                "description": alert.description,
                "time": alert.timestamp.strftime("%H:%M:%S")
            })

        return Response({
            "summary": summary,
            "employees_inside": employees_inside,
            "recent_sensor_events": sensor_events,
            "recent_alerts": alerts
        })