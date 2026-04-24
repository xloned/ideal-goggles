from django.contrib import admin
from .models import Automobile, Driver, Waybill

@admin.register(Automobile)
class AutomobileAdmin(admin.ModelAdmin):
    list_display = ['make', 'state_number', 'year', 'fuel_norm']

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['employee', 'automobile']

@admin.register(Waybill)
class WaybillAdmin(admin.ModelAdmin):
    list_display = ['pk', 'driver', 'automobile', 'departure_time', 'mileage', 'fuel_consumption']
    readonly_fields = ['mileage', 'fuel_consumption']
