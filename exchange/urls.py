"""URL-маршруты для Лаб. №3 — обмен данными."""

from django.urls import path
from . import views

app_name = 'exchange'

urlpatterns = [
    # Источник — программа 1
    path('', views.source_view, name='source'),
    path('delete/<int:pk>/', views.source_delete, name='source_delete'),

    # Сервер — программа 2
    path('server/', views.server_view, name='server'),

    # Визуализатор — программа 3
    path('visualizer/', views.visualizer_view, name='visualizer'),
    path('chart.png', views.chart_image, name='chart'),
]
