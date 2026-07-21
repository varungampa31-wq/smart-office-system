from django.urls import path
from .views import RFIDScanView

urlpatterns = [
    path("scan/rfid/", RFIDScanView.as_view(), name="rfid-scan"),
]