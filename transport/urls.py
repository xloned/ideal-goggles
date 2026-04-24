"""URL-маршруты для Лаб. №9 — учёт автотранспорта."""

from django.urls import path
from . import views

app_name = 'transport'

urlpatterns = [
    # Справочник «Автомобили»
    path('automobiles/', views.automobile_list, name='automobile_list'),
    path('automobiles/add/', views.automobile_add, name='automobile_add'),
    path('automobiles/<int:pk>/edit/', views.automobile_edit, name='automobile_edit'),
    path('automobiles/<int:pk>/delete/', views.automobile_delete, name='automobile_delete'),

    # Справочник «Водители»
    path('drivers/', views.driver_list, name='driver_list'),
    path('drivers/add/', views.driver_add, name='driver_add'),
    path('drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),
    path('drivers/<int:pk>/delete/', views.driver_delete, name='driver_delete'),

    # Журнал «Путевые листы»
    path('waybills/', views.waybill_list, name='waybill_list'),
    path('waybills/add/', views.waybill_add, name='waybill_add'),
    path('waybills/<int:pk>/edit/', views.waybill_edit, name='waybill_edit'),
    path('waybills/<int:pk>/delete/', views.waybill_delete, name='waybill_delete'),

    # AJAX
    path('api/driver/<int:driver_id>/auto/', views.get_driver_auto, name='driver_auto_api'),
]
