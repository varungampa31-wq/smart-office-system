from django.db.models import Avg, Max, Count
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import FogNodeAPIKeyAuthentication
from .permissions import IsAuthenticatedFogNode
from .models import SensorEvent
from .serializers import SensorEventSerializer
from .tasks import process_sensor_reading


class SensorEventViewSet(viewsets.ModelViewSet):
    """Human/dashboard-facing CRUD API (JWT-authenticated, unchanged
    behaviour from before). The fog node does NOT use this -- it uses
    SensorIngestView below."""
    queryset = SensorEvent.objects.all()
    serializer_class = SensorEventSerializer


class SensorIngestView(APIView):
    """
    Machine-to-machine ingestion endpoint used by the fog node.

    POST /api/sensors/ingest/
    Headers: X-API-Key: <FOG_INGEST_API_KEY>
    Body: {"readings": [ {..one reading..}, {..another..}, ... ]}

    This view intentionally does the minimum amount of work possible: it
    checks the API key, does a light shape check on the payload, and
    hands each reading off to Celery. It returns 202 Accepted (not 201)
    because nothing has actually been persisted yet at the point the
    response is sent -- that's the point of the queue: ingestion stays
    fast and cheap even if the database/worker layer is briefly slower
    or is being scaled up.
    """
    authentication_classes = [FogNodeAPIKeyAuthentication]
    permission_classes = [IsAuthenticatedFogNode]

    def post(self, request):
        readings = request.data.get("readings")

        if not isinstance(readings, list) or not readings:
            return Response(
                {"status": "failed", "message": "Expected a non-empty 'readings' list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queued = 0
        for reading in readings:
            if not isinstance(reading, dict) or "sensor_type" not in reading:
                continue
            process_sensor_reading.delay(reading)
            queued += 1

        return Response(
            {"status": "queued", "count": queued},
            status=status.HTTP_202_ACCEPTED,
        )


class SensorStatsView(APIView):
    """
    Lightweight aggregation used by the dashboard to show ambient sensor
    trends (not just raw event rows). JWT-authenticated like the rest of
    the dashboard.
    """

    def get(self, request):
        since = timezone.now() - timezone.timedelta(hours=24)
        qs = SensorEvent.objects.filter(timestamp__gte=since)

        by_type = list(
            qs.values("sensor_type").annotate(
                count=Count("id"),
                avg_value=Avg("value"),
                max_value=Max("value"),
            ).order_by("sensor_type")
        )

        latest_readings = []
        for sensor_type, _ in SensorEvent.SENSOR_CHOICES:
            latest = qs.filter(sensor_type=sensor_type).order_by("-timestamp").first()
            if latest:
                latest_readings.append({
                    "sensor_type": sensor_type,
                    "value": latest.value,
                    "unit": latest.unit,
                    "device_id": latest.device_id,
                    "event_type": latest.event_type,
                    "timestamp": latest.timestamp,
                })

        return Response({
            "window_hours": 24,
            "by_type": by_type,
            "latest_readings": latest_readings,
        })
