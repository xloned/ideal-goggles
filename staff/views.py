"""
Лабораторная работа №4 — Разграничение доступа пользователей.
Лабораторная работа №5 — Использование интернет-ресурсов (курсы валют ЦБ РФ).

Роли (группы Django):
  director  — Директор: полные права (CRUD сотрудников);
  deputy    — Заместитель: просмотр и редактирование, без удаления и добавления;
  secretary — Секретарь: только просмотр всех данных;
  (нет аккаунта) — Гость: просмотр только ФИО, должности, рабочего телефона.

Защита от брутфорса: блокировка на 5 минут после 3 неверных попыток.
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseForbidden

from .models import Employee
from .forms import EmployeeForm, LoginForm


# ─────────────────────────────────────────────────────────────
# Вспомогательные функции работы с ролями и блокировкой
# ─────────────────────────────────────────────────────────────

def get_user_role(user):
    """
    Определяет роль пользователя по принадлежности к группам Django.
    Возвращает строку: 'director', 'deputy', 'secretary' или 'guest'.
    """
    if not user.is_authenticated:
        return 'guest'
    if user.is_superuser or user.groups.filter(name='director').exists():
        return 'director'
    if user.groups.filter(name='deputy').exists():
        return 'deputy'
    if user.groups.filter(name='secretary').exists():
        return 'secretary'
    return 'guest'


def can_add(role):
    """Директор может добавлять сотрудников."""
    return role == 'director'


def can_edit(role):
    """Директор и заместитель могут редактировать."""
    return role in ('director', 'deputy')


def can_delete(role):
    """Только директор может удалять."""
    return role == 'director'


def can_view_sensitive(role):
    """Адрес и личный телефон скрыты от гостя."""
    return role in ('director', 'deputy', 'secretary')


# ─── Блокировка аккаунта ───────────────────────────────────

SESSION_ATTEMPTS_KEY = 'login_attempts'
SESSION_LOCKOUT_KEY = 'login_locked_until'
MAX_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 3)
LOCKOUT_SECONDS = getattr(settings, 'LOGIN_LOCKOUT_SECONDS', 300)


def _check_lockout(request):
    """
    Проверяет, заблокирован ли вход для данного сеанса.
    Возвращает (is_locked, seconds_remaining).
    """
    locked_until = request.session.get(SESSION_LOCKOUT_KEY, 0)
    now = time.time()
    if locked_until > now:
        return True, int(locked_until - now)
    return False, 0


def _record_failed_attempt(request):
    """
    Регистрирует неудачную попытку входа.
    Если достигнут лимит — устанавливает блокировку.
    Возвращает количество оставшихся попыток (0 = заблокировано).
    """
    attempts = request.session.get(SESSION_ATTEMPTS_KEY, 0) + 1
    request.session[SESSION_ATTEMPTS_KEY] = attempts
    if attempts >= MAX_ATTEMPTS:
        request.session[SESSION_LOCKOUT_KEY] = time.time() + LOCKOUT_SECONDS
        request.session[SESSION_ATTEMPTS_KEY] = 0
        return 0
    return MAX_ATTEMPTS - attempts


def _clear_attempts(request):
    """Сбрасывает счётчик неудачных попыток после успешного входа."""
    request.session.pop(SESSION_ATTEMPTS_KEY, None)
    request.session.pop(SESSION_LOCKOUT_KEY, None)


# ─────────────────────────────────────────────────────────────
# Аутентификация
# ─────────────────────────────────────────────────────────────

def login_view(request):
    """
    Страница входа в систему.
    Гость может перейти к просмотру без пароля (кнопка «Войти как гость»).
    При 3 неверных попытках — блокировка на 5 минут.
    """
    is_locked, seconds_left = _check_lockout(request)

    if request.method == 'POST':
        if is_locked:
            messages.error(request, f'Вход заблокирован. Попробуйте через {seconds_left} сек.')
            return render(request, 'staff/login.html', {'form': LoginForm(), 'locked': True, 'seconds_left': seconds_left})

        action = request.POST.get('action')

        # Гость — без пароля, только просмотр ограниченных данных
        if action == 'guest':
            logout(request)                         # убедимся что не авторизованы
            return redirect('staff:employee_list')

        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                _clear_attempts(request)
                return redirect('staff:employee_list')
            else:
                remaining = _record_failed_attempt(request)
                is_locked, seconds_left = _check_lockout(request)
                if is_locked:
                    messages.error(request, f'Слишком много попыток. Вход заблокирован на {LOCKOUT_SECONDS // 60} мин.')
                else:
                    messages.error(request, f'Неверный логин или пароль. Осталось попыток: {remaining}.')
    else:
        form = LoginForm()

    return render(request, 'staff/login.html', {
        'form': form,
        'locked': is_locked,
        'seconds_left': seconds_left,
    })


def logout_view(request):
    """Выход из системы."""
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('staff:login')


# ─────────────────────────────────────────────────────────────
# Список сотрудников
# ─────────────────────────────────────────────────────────────

def employee_list(request):
    """
    Список сотрудников с учётом роли пользователя.
    Гость видит только: ФИО, должность, рабочий телефон.
    Остальные роли видят все поля.
    """
    role = get_user_role(request.user)
    employees = Employee.objects.all()
    return render(request, 'staff/employee_list.html', {
        'employees': employees,
        'role': role,
        'can_add': can_add(role),
        'can_edit': can_edit(role),
        'can_delete': can_delete(role),
        'can_view_sensitive': can_view_sensitive(role),
    })


# ─────────────────────────────────────────────────────────────
# Добавление сотрудника (только Директор)
# ─────────────────────────────────────────────────────────────

@login_required
def employee_add(request):
    """
    Добавление нового сотрудника.
    Доступно только роли «Директор».
    """
    role = get_user_role(request.user)
    if not can_add(role):
        messages.error(request, 'Недостаточно прав для добавления сотрудника.')
        return redirect('staff:employee_list')

    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сотрудник добавлен.')
            return redirect('staff:employee_list')
    else:
        form = EmployeeForm()

    return render(request, 'staff/employee_form.html', {
        'form': form,
        'title': 'Добавить сотрудника',
        'role': role,
    })


# ─────────────────────────────────────────────────────────────
# Редактирование сотрудника (Директор + Заместитель)
# ─────────────────────────────────────────────────────────────

@login_required
def employee_edit(request, pk):
    """
    Редактирование данных сотрудника.
    Доступно ролям «Директор» и «Заместитель директора».
    """
    role = get_user_role(request.user)
    if not can_edit(role):
        messages.error(request, 'Недостаточно прав для редактирования.')
        return redirect('staff:employee_list')

    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные сотрудника «{employee}» обновлены.')
            return redirect('staff:employee_list')
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'staff/employee_form.html', {
        'form': form,
        'title': f'Редактировать: {employee}',
        'employee': employee,
        'role': role,
    })


# ─────────────────────────────────────────────────────────────
# Удаление сотрудника (только Директор)
# ─────────────────────────────────────────────────────────────

@login_required
def employee_delete(request, pk):
    """
    Удаление сотрудника.
    Доступно только роли «Директор».
    """
    role = get_user_role(request.user)
    if not can_delete(role):
        messages.error(request, 'Недостаточно прав для удаления.')
        return redirect('staff:employee_list')

    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        name = str(employee)
        employee.delete()
        messages.success(request, f'Сотрудник «{name}» удалён.')
        return redirect('staff:employee_list')

    return render(request, 'staff/employee_confirm_delete.html', {
        'employee': employee,
        'role': role,
    })


# ─────────────────────────────────────────────────────────────
# Лабораторная работа №5 — Курсы валют из интернета (ЦБ РФ)
# ─────────────────────────────────────────────────────────────

# Три фиксированных валюты для Варианта 1 (из задания)
PRESET_CURRENCIES = ['USD', 'EUR', 'CNY']

# URL публичного API Центрального банка России
CBR_API_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'


def currency_rates(request):
    """
    Лаб. №5, вариант 1: показ курсов трёх валют (USD, EUR, CNY) ЦБ РФ.
    Данные получаются через HTTP-запрос к API ЦБ РФ в реальном времени.

    Замена рекомендованного в задании TNMHTTP-компонента (Delphi) на
    стандартный модуль Python urllib.request.
    """
    rates = None
    error = None
    fetched_at = None

    try:
        # Загрузка актуальных курсов с сервера ЦБ РФ
        req = urllib.request.Request(CBR_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode('utf-8')
        data = json.loads(raw)

        all_valutes = data.get('Valute', {})
        fetched_at = data.get('Date', '')
        if fetched_at:
            # Форматируем дату
            try:
                dt = datetime.fromisoformat(fetched_at)
                fetched_at = dt.strftime('%d.%m.%Y %H:%M')
            except Exception:
                pass

        # Строим список только для трёх заданных валют
        rates = []
        for code in PRESET_CURRENCIES:
            v = all_valutes.get(code)
            if v:
                rates.append({
                    'code': v['CharCode'],
                    'name': v['Name'],
                    'nominal': v['Nominal'],
                    'value': v['Value'],
                    'previous': v['Previous'],
                    'change': round(v['Value'] - v['Previous'], 4),
                    'change_pct': round((v['Value'] - v['Previous']) / v['Previous'] * 100, 2),
                })

    except urllib.error.URLError as exc:
        error = f'Ошибка сети: {exc.reason}'
    except Exception as exc:
        error = f'Ошибка получения данных: {exc}'

    return render(request, 'staff/currency_rates.html', {
        'rates': rates,
        'error': error,
        'fetched_at': fetched_at,
        'preset_currencies': PRESET_CURRENCIES,
    })
