from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SensorEventViewSet, SensorIngestView, SensorStatsView

router = DefaultRouter()
router.register(r'sensors', SensorEventViewSet)

urlpatterns = [
    path('sensors/ingest/', SensorIngestView.as_view(), name='sensor-ingest'),
    path('sensors/stats/', SensorStatsView.as_view(), name='sensor-stats'),
    path('', include(router.urls)),
]
