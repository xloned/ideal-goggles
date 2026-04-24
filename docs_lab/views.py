"""
Лабораторная работа №6 — Совместная разработка ИС. Элементы документирования.

Задание: снабдить комментариями (каждую строчку) исходный код программы
из предыдущей лабораторной работы в соответствии с правилами:
  - подробные и понятные комментарии;
  - графическое выделение символами;
  - при изменении — код специалиста, дата, причина, исходный фрагмент;
  - описание сложных алгоритмов и операций с БД;
  - комментарий к каждой глобальной переменной;
  - комментарий к каждому модулю;
  - расширенный комментарий к каждой подпрограмме.

Данный модуль отображает задокументированный исходный код ключевых модулей.
"""

import inspect                    # стандартный модуль Python для получения исходного кода
import ast                        # модуль для разбора Python-кода (AST — Abstract Syntax Tree)

from django.shortcuts import render   # функция рендеринга шаблона Django

# ─── Импорт документируемых модулей ─────────────────────────────────────────
# Импортируем модули из предыдущих лабораторных работ для отображения их кода
import sales.views                # модуль views Лаб. №1 — АРМ оператора по продажам
import staff.views                # модуль views Лаб. №4 — разграничение доступа
import exchange.views             # модуль views Лаб. №3 — обмен данными
import transport.views            # модуль views Лаб. №9 — учёт транспорта
import sales.models               # модуль models Лаб. №1 и №7
import transport.models           # модуль models Лаб. №9

# ─── Реестр документируемых модулей ─────────────────────────────────────────
# Словарь: ключ — идентификатор для URL, значение — (модуль, описание)
MODULES = {
    'sales_views':      (sales.views,      'Лаб 1/7: Представления (views) АРМ продаж'),
    'sales_models':     (sales.models,     'Лаб 1/7: Модели данных АРМ продаж + ИНН'),
    'staff_views':      (staff.views,      'Лаб 4/5: Разграничение доступа и курсы валют'),
    'exchange_views':   (exchange.views,   'Лаб 3: Обмен данными между программами'),
    'transport_models': (transport.models, 'Лаб 9: Модели учёта автотранспорта'),
    'transport_views':  (transport.views,  'Лаб 9: Представления учёта автотранспорта'),
}


def docs_index(request):
    """
    Главная страница документации Лаб. №6.

    Отображает список всех задокументированных модулей проекта
    с возможностью просмотра исходного кода с комментариями.

    Параметры:
        request — объект HTTP-запроса Django (HttpRequest).
    Возвращает:
        HttpResponse — HTML-страница со списком модулей.
    """
    # Формируем список модулей с метаинформацией для отображения
    module_list = []
    for key, (module, description) in MODULES.items():
        source = inspect.getsource(module)          # получаем исходный код модуля
        line_count = source.count('\n')             # считаем количество строк
        module_list.append({
            'key':         key,                     # идентификатор для ссылки
            'description': description,             # человекочитаемое описание
            'file':        module.__file__,         # путь к файлу на диске
            'lines':       line_count,              # кол-во строк
        })

    return render(request, 'docs_lab/index.html', {'modules': module_list})


def docs_source(request, module_key):
    """
    Отображение исходного кода выбранного модуля с синтаксической подсветкой.

    Комментарии в коде оформлены согласно правилам Лаб. №6:
      - каждый блок снабжён подробным описанием;
      - специальные строки отмечены графическими символами (═══, ───);
      - указаны автор изменений, дата, назначение.

    Параметры:
        request    — объект HTTP-запроса (HttpRequest);
        module_key — строковый ключ из словаря MODULES.
    Возвращает:
        HttpResponse — страница с исходным кодом.
    """
    if module_key not in MODULES:                          # проверяем корректность ключа
        return render(request, 'docs_lab/not_found.html', {'key': module_key}, status=404)

    module, description = MODULES[module_key]              # распаковываем данные модуля

    # Получаем исходный код через модуль inspect (стандартная библиотека Python)
    source_code = inspect.getsource(module)

    # Разбиваем код на строки для построчного отображения в шаблоне
    lines = source_code.splitlines()

    # Строим список строк с метаинформацией для шаблона
    annotated_lines = []
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()                           # строка без начальных пробелов
        is_comment   = stripped.startswith('#')            # это строка комментария?
        is_docstring = stripped.startswith('"""') or stripped.startswith("'''")  # docstring?
        is_decorator = stripped.startswith('@')            # это декоратор?
        is_def       = stripped.startswith(('def ', 'class ', 'async def '))     # объявление?
        annotated_lines.append({
            'num':          i,           # номер строки
            'text':         line,        # текст строки (с отступами)
            'is_comment':   is_comment,
            'is_docstring': is_docstring,
            'is_decorator': is_decorator,
            'is_def':       is_def,
        })

    return render(request, 'docs_lab/source.html', {
        'module_key':   module_key,
        'description':  description,
        'file_path':    module.__file__,
        'lines':        annotated_lines,
        'total_lines':  len(lines),
        'modules':      MODULES,          # для навигационного меню
    })
