"""Формы для приложения transport (Лаб. №9)."""

from django import forms
from .models import Automobile, Driver, Waybill


class AutomobileForm(forms.ModelForm):
    class Meta:
        model = Automobile
        fields = ['make', 'state_number', 'year', 'fuel_norm']
        widgets = {
            'make':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Toyota Camry'}),
            'state_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'А123БВ777'}),
            'year':         forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2030}),
            'fuel_norm':    forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
        }


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['employee', 'automobile']
        widgets = {
            'employee':    forms.Select(attrs={'class': 'form-control'}),
            'automobile':  forms.Select(attrs={'class': 'form-control'}),
        }


class WaybillForm(forms.ModelForm):
    class Meta:
        model = Waybill
        fields = ['driver', 'departure_time', 'arrival_time',
                  'start_mileage', 'end_mileage']
        widgets = {
            'driver':         forms.Select(attrs={'class': 'form-control'}),
            'departure_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'arrival_time':   forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'start_mileage':  forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'end_mileage':    forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_mileage')
        end = cleaned.get('end_mileage')
        dep = cleaned.get('departure_time')
        arr = cleaned.get('arrival_time')
        if start and end and end < start:
            self.add_error('end_mileage', 'Конечный километраж не может быть меньше начального.')
        if dep and arr and arr < dep:
            self.add_error('arrival_time', 'Время заезда не может быть раньше времени выезда.')
        return cleaned
