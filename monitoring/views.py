import io
import base64
import random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import SensorConfig, SensorReading


def _get_config():
    config = SensorConfig.objects.first()
    if not config:
        config = SensorConfig.objects.create()
    return config


def _chart_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ─── Dashboard ────────────────────────────────────────────────────

def dashboard(request):
    config = _get_config()
    readings = list(config.readings.all()[:config.history_count + 1])
    current = readings[0] if readings else None
    previous = readings[1:] if len(readings) > 1 else []

    # Alerts
    warning = False
    alarm = False
    warning_msg = ""
    alarm_msg = ""

    if current and len(previous) > 0:
        prev_val = previous[0].value
        if prev_val != 0:
            change_pct = abs((current.value - prev_val) / prev_val * 100)
            if change_pct > config.warning_percent:
                warning = True
                warning_msg = f"Изменение {change_pct:.1f}% превышает порог {config.warning_percent}%"

    if current:
        if current.value < config.min_value or current.value > config.max_value:
            alarm = True
            alarm_msg = f"Значение {current.value:.2f} вне допустимого диапазона [{config.min_value}; {config.max_value}]"

    return render(request, "monitoring/dashboard.html", {
        "config": config,
        "current": current,
        "previous": previous,
        "warning": warning,
        "warning_msg": warning_msg,
        "alarm": alarm,
        "alarm_msg": alarm_msg,
    })


def dashboard_v2(request):
    config = _get_config()
    readings = list(config.readings.all()[:config.history_count + 1])
    current = readings[0] if readings else None
    previous = readings[1:] if len(readings) > 1 else []

    warning = False
    alarm = False
    warning_msg = ""
    alarm_msg = ""

    if current and len(previous) > 0:
        prev_val = previous[0].value
        if prev_val != 0:
            change_pct = abs((current.value - prev_val) / prev_val * 100)
            if change_pct > config.warning_percent:
                warning = True
                warning_msg = f"Изменение {change_pct:.1f}% превышает порог {config.warning_percent}%"

    if current:
        if current.value < config.min_value or current.value > config.max_value:
            alarm = True
            alarm_msg = f"Значение {current.value:.2f} вне допустимого диапазона [{config.min_value}; {config.max_value}]"

    return render(request, "monitoring/v2/dashboard.html", {
        "config": config,
        "current": current,
        "previous": previous,
        "warning": warning,
        "warning_msg": warning_msg,
        "alarm": alarm,
        "alarm_msg": alarm_msg,
    })


# ─── Generate new reading ────────────────────────────────────────

def generate_reading(request):
    config = _get_config()
    last = config.readings.first()
    if last:
        base = last.value
        delta = random.uniform(-5, 5)
        # Occasionally generate out-of-range values
        if random.random() < 0.15:
            delta = random.choice([-1, 1]) * random.uniform(10, 20)
        new_val = round(base + delta, 2)
    else:
        new_val = round(random.uniform(config.min_value, config.max_value), 2)

    SensorReading.objects.create(config=config, value=new_val)

    redirect_url = request.GET.get("next", "/monitoring/")
    return redirect(redirect_url)


# ─── Config edit ──────────────────────────────────────────────────

def config_edit(request):
    config = _get_config()
    if request.method == "POST":
        config.name = request.POST.get("name", config.name)
        config.unit = request.POST.get("unit", config.unit)
        config.min_value = float(request.POST.get("min_value", config.min_value))
        config.max_value = float(request.POST.get("max_value", config.max_value))
        config.warning_percent = float(request.POST.get("warning_percent", config.warning_percent))
        config.history_count = int(request.POST.get("history_count", config.history_count))
        config.save()
        return redirect("monitoring_dashboard")
    return render(request, "monitoring/config.html", {"config": config})


def config_edit_v2(request):
    config = _get_config()
    if request.method == "POST":
        config.name = request.POST.get("name", config.name)
        config.unit = request.POST.get("unit", config.unit)
        config.min_value = float(request.POST.get("min_value", config.min_value))
        config.max_value = float(request.POST.get("max_value", config.max_value))
        config.warning_percent = float(request.POST.get("warning_percent", config.warning_percent))
        config.history_count = int(request.POST.get("history_count", config.history_count))
        config.save()
        return redirect("monitoring_dashboard_v2")
    return render(request, "monitoring/v2/config.html", {"config": config})


# ─── API: data for JS ────────────────────────────────────────────

def api_data(request):
    config = _get_config()
    readings = list(config.readings.all()[:50])
    data = [
        {"value": r.value, "time": r.timestamp.strftime("%H:%M:%S")}
        for r in reversed(readings)
    ]
    return JsonResponse({
        "readings": data,
        "config": {
            "name": config.name,
            "unit": config.unit,
            "min": config.min_value,
            "max": config.max_value,
            "warning_pct": config.warning_percent,
        },
    })


# ─── Charts via matplotlib ───────────────────────────────────────

def chart_current(request):
    """Line chart of all current readings."""
    config = _get_config()
    readings = list(config.readings.all()[:config.history_count + 1])
    readings.reverse()

    if not readings:
        return HttpResponse(status=204)

    values = [r.value for r in readings]
    labels = [r.timestamp.strftime("%H:%M:%S") for r in readings]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(labels, values, "o-", color="#3b82f6", linewidth=2, markersize=5)
    ax.axhline(y=config.min_value, color="#ef4444", linestyle="--", linewidth=1, label=f"Мин ({config.min_value})")
    ax.axhline(y=config.max_value, color="#ef4444", linestyle="--", linewidth=1, label=f"Макс ({config.max_value})")
    ax.fill_between(range(len(values)), config.min_value, config.max_value, alpha=0.08, color="#22c55e")
    ax.set_title(f"График: {config.name} ({config.unit})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Время")
    ax.set_ylabel(config.unit)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()

    img = _chart_to_base64(fig)
    return JsonResponse({"image": img})


def chart_filtered(request):
    """Line chart of filtered (selected) readings + red average line."""
    config = _get_config()
    readings = list(config.readings.all()[:50])
    readings.reverse()

    mode = request.GET.get("mode", "gt")  # gt, lt, multiple
    boundary = float(request.GET.get("boundary", "25"))

    values = [r.value for r in readings]
    labels = [r.timestamp.strftime("%H:%M:%S") for r in readings]

    if mode == "gt":
        filtered = [(l, v) for l, v in zip(labels, values) if v > boundary]
    elif mode == "lt":
        filtered = [(l, v) for l, v in zip(labels, values) if v < boundary]
    elif mode == "multiple":
        mult = int(boundary) if boundary != 0 else 1
        filtered = [(l, v) for l, v in zip(labels, values) if int(v) % mult == 0]
    else:
        filtered = list(zip(labels, values))

    if not filtered:
        return JsonResponse({"image": "", "count": 0, "avg": 0})

    f_labels, f_values = zip(*filtered)
    avg = float(np.mean(f_values))

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(f_labels, f_values, "s-", color="#8b5cf6", linewidth=2, markersize=5)
    ax.axhline(y=avg, color="#ef4444", linewidth=2, linestyle="-", label=f"Среднее: {avg:.2f}")
    ax.set_title("Выборочные значения", fontsize=13, fontweight="bold")
    ax.set_xlabel("Время")
    ax.set_ylabel(config.unit)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()

    img = _chart_to_base64(fig)
    return JsonResponse({"image": img, "count": len(f_values), "avg": round(avg, 2)})


def chart_bar(request):
    """Bar chart of filtered readings."""
    config = _get_config()
    readings = list(config.readings.all()[:50])
    readings.reverse()

    mode = request.GET.get("mode", "gt")
    boundary = float(request.GET.get("boundary", "25"))

    values = [r.value for r in readings]
    labels = [r.timestamp.strftime("%H:%M:%S") for r in readings]

    if mode == "gt":
        filtered = [(l, v) for l, v in zip(labels, values) if v > boundary]
    elif mode == "lt":
        filtered = [(l, v) for l, v in zip(labels, values) if v < boundary]
    elif mode == "multiple":
        mult = int(boundary) if boundary != 0 else 1
        filtered = [(l, v) for l, v in zip(labels, values) if int(v) % mult == 0]
    else:
        filtered = list(zip(labels, values))

    if not filtered:
        return JsonResponse({"image": "", "count": 0})

    f_labels, f_values = zip(*filtered)
    avg = float(np.mean(f_values))

    fig, ax = plt.subplots(figsize=(8, 3.5))
    colors = ["#ef4444" if v > config.max_value or v < config.min_value else "#3b82f6" for v in f_values]
    ax.bar(f_labels, f_values, color=colors, width=0.6)
    ax.axhline(y=avg, color="#ef4444", linewidth=2, linestyle="-", label=f"Среднее: {avg:.2f}")
    ax.set_title("Диаграмма выборочных значений", fontsize=13, fontweight="bold")
    ax.set_xlabel("Время")
    ax.set_ylabel(config.unit)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()

    img = _chart_to_base64(fig)
    return JsonResponse({"image": img, "count": len(f_values)})
