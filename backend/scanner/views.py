from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from employees.models import Employee
from attendance.models import Attendance
from sensors.models import SensorEvent
from alerts.models import Alert


class RFIDScanView(APIView):
    """
    Human-facing "badge scan" simulator used by the frontend's scanner
    page. This is a convenience path for demoing/testing the attendance
    flow from a browser button click and is independent of the fog
    ingestion pipeline (sensors/views.py: SensorIngestView), which is
    what the autonomous sensor simulators/fog node use.

    NOTE: sensor_type/event_type values below were corrected to match
    SensorEvent.SENSOR_CHOICES / EVENT_CHOICES (they previously used
    free-text labels like "RFID Reader" that didn't match any choice).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        rfid_tag = request.data.get("rfid_tag")

        if not rfid_tag:
            return Response(
                {
                    "status": "failed",
                    "message": "RFID Tag is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Find Employee
        # ----------------------------------------------------

        try:
            employee = Employee.objects.get(rfid_tag=rfid_tag)

        except Employee.DoesNotExist:

            # RFID Reader detects invalid card
            SensorEvent.objects.create(
                employee=None,
                sensor_type="RFID",
                event_type="INVALID_RFID",
                device_id="RFID_READER_01",
                processed=True,
                raw_data={"scanned_tag": rfid_tag},
            )

            # Door remains locked
            SensorEvent.objects.create(
                employee=None,
                sensor_type="DOOR",
                event_type="ACCESS_DENIED",
                device_id="LOCK_SENSOR_01",
                processed=True
            )

            Alert.objects.create(
                employee=None,
                alert_type="INVALID_RFID",
                severity="HIGH",
                description=f"Unknown RFID scanned: {rfid_tag}"
            )

            return Response(
                {
                    "status": "failed",
                    "message": "Invalid RFID Tag"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        today = timezone.now().date()
        now = timezone.now()

        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={
                "check_in": now,
                "status": "Present"
            }
        )

        # ----------------------------------------------------
        # FIRST SCAN = CHECK IN
        # ----------------------------------------------------

        if created:

            SensorEvent.objects.bulk_create([

                SensorEvent(
                    employee=employee,
                    sensor_type="RFID",
                    event_type="RFID_SCAN",
                    device_id="RFID_READER_01",
                    processed=True
                ),

                SensorEvent(
                    employee=employee,
                    sensor_type="DOOR",
                    event_type="DOOR_OPEN",
                    device_id="DOOR_SENSOR_01",
                    processed=True
                ),

                SensorEvent(
                    employee=employee,
                    sensor_type="DOOR",
                    event_type="ACCESS_GRANTED",
                    device_id="LOCK_SENSOR_01",
                    processed=True
                ),

                SensorEvent(
                    employee=employee,
                    sensor_type="OCCUPANCY",
                    event_type="ENTRY_DETECTED",
                    device_id="OCC_SENSOR_01",
                    processed=True
                ),

                SensorEvent(
                    employee=employee,
                    sensor_type="CAMERA",
                    event_type="FACE_VERIFIED",
                    device_id="CAMERA_01",
                    processed=True
                ),

            ])

            return Response({
                "status": "success",
                "action": "CHECK_IN",
                "employee": {
                    "employee_id": employee.employee_id,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "department": employee.department
                }
            })

        # ----------------------------------------------------
        # SECOND SCAN = CHECK OUT
        # ----------------------------------------------------

        if attendance.check_out is None:

            attendance.check_out = now

            duration = attendance.check_out - attendance.check_in
            attendance.working_hours = round(duration.total_seconds() / 3600, 2)

            attendance.save()

            SensorEvent.objects.bulk_create([

                SensorEvent(
                    employee=employee,
                    sensor_type="RFID",
                    event_type="RFID_SCAN",
                    device_id="RFID_READER_01",
                    processed=True
                ),

                SensorEvent(
                    employee=employee,
                    sensor_type="DOOR",
                    event_type="DOOR_OPEN",
                    device_id="DOOR_SENSOR_01",
                    processed=True
                ),

                SensorEvent(
                    employee=employee,
                    sensor_type="DOOR",
                    event_type="ACCESS_GRANTED",
                    device_id="LOCK_SENSOR_01",
                    processed=True
                ),

                SensorEvent(
                    employee=employee,
                    sensor_type="OCCUPANCY",
                    event_type="EXIT_DETECTED",
                    device_id="OCC_SENSOR_01",
                    processed=True
                ),

            ])

            return Response({
                "status": "success",
                "action": "CHECK_OUT",
                "employee": {
                    "employee_id": employee.employee_id,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "department": employee.department
                }
            })

        # ----------------------------------------------------
        # ALREADY CHECKED OUT
        # ----------------------------------------------------

        SensorEvent.objects.bulk_create([

            SensorEvent(
                employee=employee,
                sensor_type="RFID",
                event_type="RFID_SCAN",
                device_id="RFID_READER_01",
                processed=True
            ),

            SensorEvent(
                employee=employee,
                sensor_type="DOOR",
                event_type="ACCESS_DENIED",
                device_id="LOCK_SENSOR_01",
                processed=True
            ),

        ])

        Alert.objects.create(
            employee=employee,
            alert_type="MULTIPLE_SCAN",
            severity="MEDIUM",
            description="Employee attempted to scan after checkout."
        )

        return Response(
            {
                "status": "warning",
                "message": "Employee has already checked out today.",
                "employee": {
                    "employee_id": employee.employee_id,
                    "name": f"{employee.first_name} {employee.last_name}"
                }
            },
            status=status.HTTP_200_OK
        )
