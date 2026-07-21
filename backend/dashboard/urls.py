from django.urls import path
from .views import DashboardSummaryView, LiveDashboardView

urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/live/", LiveDashboardView.as_view(), name="dashboard-live"),
]