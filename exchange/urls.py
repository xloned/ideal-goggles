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

    # Экспорт в Excel (Лаб 3 — аналог OLE-диаграммы в Microsoft Excel)
    path('export/excel/', views.export_excel, name='export_excel'),

    # ── Вариант 4 (Дизайн 2): датчики температуры ──────────────
    path('v4/',                   views.source_v4_view,    name='source_v4'),
    path('v4/delete/<int:pk>/',   views.source_v4_delete,  name='source_v4_delete'),
    path('v4/server/',            views.server_v4_view,    name='server_v4'),
    path('v4/visualizer/',        views.visualizer_v4_view,name='visualizer_v4'),
    path('v4/chart.png',          views.chart_image_v4,    name='chart_v4'),
    path('v4/export/excel/',      views.export_excel_v4,   name='export_excel_v4'),
]
