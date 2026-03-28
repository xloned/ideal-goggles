from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="monitoring_dashboard"),
    path("generate/", views.generate_reading, name="monitoring_generate"),
    path("api/data/", views.api_data, name="monitoring_api_data"),
    path("api/chart/current/", views.chart_current, name="monitoring_chart_current"),
    path("api/chart/filtered/", views.chart_filtered, name="monitoring_chart_filtered"),
    path("api/chart/bar/", views.chart_bar, name="monitoring_chart_bar"),
    path("config/", views.config_edit, name="monitoring_config"),
    # V2
    path("v2/", views.dashboard_v2, name="monitoring_dashboard_v2"),
    path("v2/config/", views.config_edit_v2, name="monitoring_config_v2"),
]
