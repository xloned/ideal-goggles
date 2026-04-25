"""
Лабораторная работа №9 — Новые информационные объекты.
Учёт пробега автотранспорта: справочники, путевые листы, статистика.
"""

import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum, Count, Avg
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


# ── Статистика / Диаграммы ──────────────────────────────────

def statistics(request):
    """
    Страница статистики Лаб. №9.
    Показывает сводную таблицу и ссылки на диаграммы:
      • Гистограмма пробега по автомобилям
      • Гистограмма расхода топлива по водителям
      • Диаграмма кол-ва поездок по автомобилям
    """
    # Пробег по автомобилям
    autos_stats = (
        Automobile.objects
        .annotate(
            total_mileage=Sum('waybills__mileage'),
            total_fuel=Sum('waybills__fuel_consumption'),
            trips=Count('waybills'),
        )
        .order_by('-total_mileage')
    )

    # Пробег по водителям
    drivers_stats = (
        Driver.objects
        .select_related('employee', 'automobile')
        .annotate(
            total_mileage=Sum('waybills__mileage'),
            total_fuel=Sum('waybills__fuel_consumption'),
            trips=Count('waybills'),
        )
        .order_by('-total_mileage')
    )

    # Общая сводка
    totals = Waybill.objects.aggregate(
        total_mileage=Sum('mileage'),
        total_fuel=Sum('fuel_consumption'),
        total_trips=Count('id'),
    )

    return render(request, 'transport/statistics.html', {
        'autos_stats': autos_stats,
        'drivers_stats': drivers_stats,
        'totals': totals,
    })


def chart_mileage_by_auto(request):
    """Гистограмма: суммарный пробег по каждому автомобилю (PNG)."""
    data = (
        Automobile.objects
        .annotate(total_mileage=Sum('waybills__mileage'))
        .filter(total_mileage__isnull=False)
        .order_by('-total_mileage')
    )

    labels = [f"{a.make}\n{a.state_number}" for a in data]
    values = [float(a.total_mileage or 0) for a in data]

    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 1.4), 5))
    colors = plt.cm.Blues(np.linspace(0.45, 0.9, max(len(values), 1)))[::-1]
    bars = ax.bar(labels, values, color=colors, edgecolor='#1F4E79', linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                f'{val:,.0f} км', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_title('Пробег по автомобилям', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Пробег (км)', fontsize=11)
    ax.set_xlabel('Автомобиль', fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def chart_fuel_by_driver(request):
    """Гистограмма: расход топлива по водителям (PNG)."""
    data = (
        Driver.objects
        .select_related('employee')
        .annotate(total_fuel=Sum('waybills__fuel_consumption'))
        .filter(total_fuel__isnull=False)
        .order_by('-total_fuel')
    )

    labels = [d.employee.full_name for d in data]
    values = [float(d.total_fuel or 0) for d in data]

    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 1.4), 5))
    colors = plt.cm.Oranges(np.linspace(0.4, 0.85, max(len(values), 1)))[::-1]
    bars = ax.bar(labels, values, color=colors, edgecolor='#7B3F00', linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                f'{val:,.1f} л', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_title('Расход топлива по водителям', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Расход топлива (л)', fontsize=11)
    ax.set_xlabel('Водитель', fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def chart_trips_pie(request):
    """Круговая диаграмма: доля поездок по автомобилям (PNG)."""
    data = (
        Automobile.objects
        .annotate(trips=Count('waybills'))
        .filter(trips__gt=0)
        .order_by('-trips')
    )

    labels = [f"{a.make} {a.state_number}" for a in data]
    values = [a.trips for a in data]

    fig, ax = plt.subplots(figsize=(7, 5))
    palette = plt.cm.Set3(np.linspace(0, 1, max(len(values), 1)))
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct='%1.0f%%',
        colors=palette, startangle=140,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight('bold')

    ax.legend(wedges, [f"{l} ({v} поездок)" for l, v in zip(labels, values)],
              loc='lower left', fontsize=8, framealpha=0.8)
    ax.set_title('Распределение поездок по автомобилям',
                 fontsize=13, fontweight='bold', pad=15)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')
