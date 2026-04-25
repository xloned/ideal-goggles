"""
Telegram-бот для Лаб 5 и Лаб 11.

Лаб 5  — «Использование информационных ресурсов Internet»:
  Бот получает курсы валют через CBR JSON API (cbr-xml-daily.ru)
  и отвечает на запросы пользователя.

Лаб 11 — «Проектирование элементов CASE-систем»:
  Мини CASE-система: пользователь визуально компонует цепочку
  математических функций y = F1(F2(F3(x))), где каждая Fi выбирается
  из набора {y=x, y=1/x, y=e^x}.
  Бот генерирует рабочий Python-код для вычисления заданного выражения.

Запуск:
  python manage.py run_bot --token <BOT_TOKEN>
или задать переменную окружения TELEGRAM_BOT_TOKEN.
"""

import math
import urllib.request
import urllib.error
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────
# Лаб 5: Курсы валют через CBR API
# ─────────────────────────────────────────────────
CBR_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
PRESET_CURRENCIES = ['USD', 'EUR', 'CNY', 'GBP', 'JPY']
CURRENCY_NAMES = {
    'USD': 'Доллар США',
    'EUR': 'Евро',
    'CNY': 'Китайский юань',
    'GBP': 'Британский фунт',
    'JPY': 'Японская иена',
    'CHF': 'Швейцарский франк',
    'BYR': 'Белорусский рубль',
    'TRY': 'Турецкая лира',
    'KZT': 'Казахстанский тенге',
}


def fetch_rates():
    """Получить курсы валют с сервера ЦБ РФ."""
    try:
        req = urllib.request.Request(CBR_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data
    except Exception as e:
        logger.error('CBR API error: %s', e)
        return None


def format_rate(code: str, info: dict) -> str:
    val   = info.get('Value', 0)
    prev  = info.get('Previous', 0)
    nom   = info.get('Nominal', 1)
    diff  = val - prev
    arrow = '📈' if diff > 0 else ('📉' if diff < 0 else '➡️')
    name  = info.get('Name', code)
    rate_per_unit = val / nom
    diff_per_unit = diff / nom
    return (
        f"<b>{code}</b> — {name}\n"
        f"  {nom} {code} = <b>{val:.4f} ₽</b>\n"
        f"  1 {code} = {rate_per_unit:.4f} ₽  "
        f"{arrow} {'+' if diff_per_unit >= 0 else ''}{diff_per_unit:.4f} ₽"
    )


def build_rates_message(data: dict, codes=None) -> str:
    """Сформировать текстовое сообщение с курсами."""
    valutes = data.get('Valute', {})
    date_str = data.get('Date', '')[:10]
    lines = [f"<b>Курсы ЦБ РФ на {date_str}</b>\n"]
    targets = codes or PRESET_CURRENCIES
    for code in targets:
        code = code.upper()
        if code in valutes:
            lines.append(format_rate(code, valutes[code]))
        else:
            lines.append(f"<b>{code}</b> — не найдена")
        lines.append('')
    lines.append('<i>Источник: cbr-xml-daily.ru</i>')
    return '\n'.join(lines)


# ─────────────────────────────────────────────────
# Лаб 11: CASE-система
# ─────────────────────────────────────────────────

FUNCTIONS = {
    'identity': {
        'label': 'y = x',
        'code': 'lambda x: x',
        'fn': lambda x: x,
        'domain': lambda x: True,
        'domain_err': '',
    },
    'inverse': {
        'label': 'y = 1/x',
        'code': 'lambda x: 1 / x',
        'fn': lambda x: 1 / x,
        'domain': lambda x: x != 0,
        'domain_err': 'x ≠ 0',
    },
    'exp': {
        'label': 'y = eˣ',
        'code': 'lambda x: math.exp(x)',
        'fn': lambda x: math.exp(x),
        'domain': lambda x: True,
        'domain_err': '',
    },
}

# Хранилище состояния сессий CASE (в памяти, т.к. бот stateless между рестартами)
# {user_id: {'step': int, 'funcs': [key, key, key]}}
case_sessions = {}


def case_compute(f1_key, f2_key, f3_key, x_val):
    """
    Вычислить y = F1(F2(F3(x))).
    Возвращает (result, error_message).
    Вычисление пошаговое: проверяем область определения каждой функции
    для реального аргумента (результата предыдущей).
    """
    try:
        f3_spec = FUNCTIONS[f3_key]
        f2_spec = FUNCTIONS[f2_key]
        f1_spec = FUNCTIONS[f1_key]

        # Шаг 1: F3(x)
        if not f3_spec['domain'](x_val):
            return None, f"Ошибка: F3 ({f3_spec['label']}) не определена: {f3_spec['domain_err']}"
        v3 = f3_spec['fn'](x_val)

        # Шаг 2: F2(v3)
        if not f2_spec['domain'](v3):
            return None, f"Ошибка: F2 ({f2_spec['label']}) не определена при x={v3} ({f2_spec['domain_err']})"
        v2 = f2_spec['fn'](v3)

        # Шаг 3: F1(v2)
        if not f1_spec['domain'](v2):
            return None, f"Ошибка: F1 ({f1_spec['label']}) не определена при x={v2} ({f1_spec['domain_err']})"
        v1 = f1_spec['fn'](v2)

        return v1, None
    except ZeroDivisionError:
        return None, 'Деление на ноль.'
    except OverflowError:
        return None, 'Переполнение: слишком большое число.'
    except Exception as e:
        return None, f'Ошибка вычисления: {e}'


def case_generate_code(f1_key, f2_key, f3_key) -> str:
    """
    Лаб 11 — генерация Python-кода для заданной цепочки функций.
    Аналог генерации VBA-кода из оригинального задания.
    """
    f3 = FUNCTIONS[f3_key]
    f2 = FUNCTIONS[f2_key]
    f1 = FUNCTIONS[f1_key]

    code = f'''import math

# === Сгенерировано CASE-системой (Лаб 11) ===
# Функциональная цепочка: y = F1(F2(F3(x)))
# F1: {f1["label"]}
# F2: {f2["label"]}
# F3: {f3["label"]}

F3 = {f3["code"]}
F2 = {f2["code"]}
F1 = {f1["code"]}

def compute(x):
    """Вычислить y = F1(F2(F3(x)))."""
    v3 = F3(x)
    v2 = F2(v3)
    v1 = F1(v2)
    return v1

# Пример использования:
if __name__ == "__main__":
    x = float(input("Введите x: "))
    try:
        y = compute(x)
        print(f"y = {{y}}")
    except ZeroDivisionError:
        print("Ошибка: деление на ноль")
    except OverflowError:
        print("Ошибка: переполнение")
'''
    return code
