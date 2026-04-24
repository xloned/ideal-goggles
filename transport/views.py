"""
Лабораторная работа №9 — Новые информационные объекты.
Учёт пробега автотранспорта: справочники и путевые листы.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from decimal import Decimal

from .models import Automobile, Driver, Waybill
from .forms import AutomobileForm, DriverForm, WaybillForm


# ── Справочник «Автомобили» ─────────────────────────────────

def automobile_list(request):
    """Список всех автомобилей с суммарным пробегом."""
    autos = Automobile.objects.annotate(
        total_mileage=Sum('waybills__mileage'),
        trips_count=Count('waybills'),
    )
    return render(request, 'transport/automobile_list.html', {'automobiles': autos})


def automobile_add(request):
    """Добавление нового автомобиля в справочник."""
    if request.method == 'POST':
        form = AutomobileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Автомобиль добавлен.')
            return redirect('transport:automobile_list')
    else:
        form = AutomobileForm()
    return render(request, 'transport/automobile_form.html', {'form': form, 'title': 'Добавить автомобиль'})


def automobile_edit(request, pk):
    """Редактирование данных автомобиля."""
    auto = get_object_or_404(Automobile, pk=pk)
    if request.method == 'POST':
        form = AutomobileForm(request.POST, instance=auto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные «{auto}» обновлены.')
            return redirect('transport:automobile_list')
    else:
        form = AutomobileForm(instance=auto)
    return render(request, 'transport/automobile_form.html', {'form': form, 'title': f'Редактировать: {auto}'})


def automobile_delete(request, pk):
    """Удаление автомобиля (с подтверждением)."""
    auto = get_object_or_404(Automobile, pk=pk)
    if request.method == 'POST':
        name = str(auto)
        auto.delete()
        messages.success(request, f'Автомобиль «{name}» удалён.')
        return redirect('transport:automobile_list')
    return render(request, 'transport/confirm_delete.html', {'obj': auto, 'type': 'Автомобиль'})


# ── Справочник «Водители» ───────────────────────────────────

def driver_list(request):
    """Список водителей с закреплёнными автомобилями."""
    drivers = Driver.objects.select_related('employee', 'automobile').all()
    return render(request, 'transport/driver_list.html', {'drivers': drivers})


def driver_add(request):
    """Добавление записи водителя."""
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Водитель добавлен.')
            return redirect('transport:driver_list')
    else:
        form = DriverForm()
    return render(request, 'transport/driver_form.html', {'form': form, 'title': 'Добавить водителя'})


def driver_edit(request, pk):
    """Редактирование водителя."""
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные водителя «{driver}» обновлены.')
            return redirect('transport:driver_list')
    else:
        form = DriverForm(instance=driver)
    return render(request, 'transport/driver_form.html', {'form': form, 'title': f'Редактировать: {driver}'})


def driver_delete(request, pk):
    """Удаление водителя."""
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        name = str(driver)
        driver.delete()
        messages.success(request, f'Водитель «{name}» удалён.')
        return redirect('transport:driver_list')
    return render(request, 'transport/confirm_delete.html', {'obj': driver, 'type': 'Водитель'})


# ── Документ «Путевой лист» ─────────────────────────────────

def waybill_list(request):
    """Журнал путевых листов с итоговой статистикой."""
    waybills = Waybill.objects.select_related('driver__employee', 'automobile').all()
    stats = waybills.aggregate(
        total_mileage=Sum('mileage'),
        total_fuel=Sum('fuel_consumption'),
        total_count=Count('id'),
    )
    return render(request, 'transport/waybill_list.html', {
        'waybills': waybills,
        'stats': stats,
    })


def waybill_add(request):
    """Создание нового путевого листа."""
    if request.method == 'POST':
        form = WaybillForm(request.POST)
        if form.is_valid():
            wb = form.save(commit=False)
            # Автозаполнение автомобиля из профиля водителя
            if wb.driver and wb.driver.automobile:
                wb.automobile = wb.driver.automobile
            wb.save()
            messages.success(request, f'Путевой лист №{wb.pk} создан.')
            return redirect('transport:waybill_list')
    else:
        form = WaybillForm()
    return render(request, 'transport/waybill_form.html', {'form': form, 'title': 'Новый путевой лист'})


def waybill_edit(request, pk):
    """Редактирование (закрытие) путевого листа — ввод конечного километража."""
    wb = get_object_or_404(Waybill, pk=pk)
    if request.method == 'POST':
        form = WaybillForm(request.POST, instance=wb)
        if form.is_valid():
            form.save()
            messages.success(request, f'Путевой лист №{wb.pk} обновлён. Пробег: {wb.mileage} км.')
            return redirect('transport:waybill_list')
    else:
        form = WaybillForm(instance=wb)
    return render(request, 'transport/waybill_form.html', {
        'form': form, 'title': f'Путевой лист №{wb.pk}', 'waybill': wb
    })


def waybill_delete(request, pk):
    """Удаление путевого листа."""
    wb = get_object_or_404(Waybill, pk=pk)
    if request.method == 'POST':
        num = wb.pk
        wb.delete()
        messages.success(request, f'Путевой лист №{num} удалён.')
        return redirect('transport:waybill_list')
    return render(request, 'transport/confirm_delete.html', {'obj': wb, 'type': 'Путевой лист'})


# ── AJAX: автозаполнение автомобиля при выборе водителя ─────

def get_driver_auto(request, driver_id):
    """
    AJAX-endpoint: возвращает JSON с данными автомобиля водителя.
    Используется на форме путевого листа для автозаполнения поля «Автомобиль»
    при выборе водителя — аналог события OnChange в Delphi-задании.
    """
    from django.http import JsonResponse
    try:
        driver = Driver.objects.select_related('automobile').get(pk=driver_id)
        if driver.automobile:
            auto = driver.automobile
            data = {'id': auto.pk, 'name': str(auto), 'fuel_norm': float(auto.fuel_norm)}
        else:
            data = {'id': None, 'name': 'Не назначен', 'fuel_norm': None}
    except Driver.DoesNotExist:
        data = {'id': None, 'name': '', 'fuel_norm': None}
    return JsonResponse(data)
