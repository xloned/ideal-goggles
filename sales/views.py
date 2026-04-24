"""
АРМ оператора по продажам — представления (views).

Лаб. №1: ввод и обработка данных о клиентах, товарах, заказах.
Лаб. №7: добавлено поле ИНН, валидация, проверка дублей (validate_inn, check_duplicate_inn).
Лаб. №8: добавлены функции экспорта в PDF (pdf_order, pdf_report, pdf_clients).

Автор изменений Лаб. №7–8: студент группы, дата: апрель 2026.
"""

import io                           # для BytesIO-буфера PDF
import json                         # парсинг JSON из форм заказа
from decimal import Decimal         # точная арифметика для денежных сумм

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from django.contrib import messages

# ─── Импорт reportlab для генерации PDF (Лаб. №8) ───────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

from .models import Client, Product, Order, OrderItem

# ─── Регистрация шрифта с поддержкой кириллицы ──────────────────────────────
# Ищем DejaVuSans (есть в большинстве Linux/macOS систем)
_FONT_PATHS = [
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf',
]
_PDF_FONT = 'Helvetica'             # запасной шрифт (без кириллицы в имени)
for _fp in _FONT_PATHS:
    if os.path.exists(_fp):
        try:
            pdfmetrics.registerFont(TTFont('CustomFont', _fp))
            _PDF_FONT = 'CustomFont'
        except Exception:
            pass
        break


def index(request):
    return render(request, "sales/index.html")


# ─── Clients ────────────────────────────────────────────────────────

def client_list(request):
    query = request.GET.get("q", "")
    clients = Client.objects.all()
    if query:
        clients = clients.filter(name__icontains=query)
    return render(request, "sales/client_list.html", {"clients": clients, "query": query})


def client_search_api(request):
    q = request.GET.get("q", "")
    clients = Client.objects.filter(name__icontains=q)[:10] if q else []
    data = [
        {
            "id": c.id,
            "name": c.name,
            "total_purchases": str(c.total_purchases),
            "current_account": str(c.current_account),
            "credit_limit": str(c.credit_limit),
            "current_debt": str(c.current_debt),
            "credit_remaining": str(c.credit_remaining),
            "comment": c.comment,
            "debt_warning": c.debt_warning,
        }
        for c in clients
    ]
    return JsonResponse(data, safe=False)


def client_add(request):
    if request.method == "POST":
        inn = request.POST.get("inn", "").strip()
        # ── Лаб. №7: проверка дубля ИНН перед сохранением ──────────────────
        if inn and Client.objects.filter(inn=inn).exists():
            messages.warning(request, f'Клиент с ИНН {inn} уже существует в базе!')
        Client.objects.create(
            name=request.POST["name"],
            inn=inn,
            total_purchases=Decimal(request.POST.get("total_purchases", "0")),
            current_account=Decimal(request.POST.get("current_account", "0")),
            credit_limit=Decimal(request.POST.get("credit_limit", "0")),
            current_debt=Decimal(request.POST.get("current_debt", "0")),
            comment=request.POST.get("comment", ""),
        )
        return redirect("client_list")
    return render(request, "sales/client_form.html")


def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        inn = request.POST.get("inn", "").strip()
        # ── Лаб. №7: проверка дубля ИНН (исключаем текущего клиента) ────────
        if inn and Client.objects.filter(inn=inn).exclude(pk=pk).exists():
            messages.warning(request, f'Другой клиент с ИНН {inn} уже существует в базе!')
        client.name = request.POST["name"]
        client.inn = inn
        client.total_purchases = Decimal(request.POST.get("total_purchases", "0"))
        client.current_account = Decimal(request.POST.get("current_account", "0"))
        client.credit_limit = Decimal(request.POST.get("credit_limit", "0"))
        client.current_debt = Decimal(request.POST.get("current_debt", "0"))
        client.comment = request.POST.get("comment", "")
        client.save()
        return redirect("client_list")
    return render(request, "sales/client_form.html", {"client": client})


# ── Лаб. №7: AJAX-проверка дублирующихся ИНН в базе ─────────────────────────
def check_duplicate_inn(request):
    """
    Лаб. №7: Проверка дублей ИНН в базе данных клиентов.
    AJAX GET: ?inn=XXXXXXXX[&exclude_id=N]
    Возвращает JSON: {duplicate: true/false, client_name: '...'}
    """
    inn = request.GET.get('inn', '').strip()
    exclude_id = request.GET.get('exclude_id')
    if not inn:
        return JsonResponse({'duplicate': False})
    qs = Client.objects.filter(inn=inn)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    dup = qs.first()
    if dup:
        return JsonResponse({'duplicate': True, 'client_name': dup.name})
    return JsonResponse({'duplicate': False})


# ─── Products ───────────────────────────────────────────────────────

def product_list(request):
    products = Product.objects.all()
    return render(request, "sales/product_list.html", {"products": products})


def product_add(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        price_str = request.POST.get("price", "0")
        stock_str = request.POST.get("stock", "0")
        errors = []
        if not name:
            errors.append("Наименование товара не заполнено.")
        try:
            price = Decimal(price_str)
            if price <= 0:
                errors.append("Цена должна быть больше нуля.")
        except Exception:
            errors.append("Некорректная цена.")
            price = Decimal("0")
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append("Количество не может быть отрицательным.")
        except Exception:
            errors.append("Некорректное количество.")
            stock = 0
        if errors:
            form_data = {"name": name, "price": price_str, "stock": stock_str}
            return render(request, "sales/product_form.html", {"errors": errors, "form_data": form_data})
        Product.objects.create(name=name, price=price, stock=stock)
        return redirect("product_list")
    return render(request, "sales/product_form.html")


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        price_str = request.POST.get("price", "0")
        stock_str = request.POST.get("stock", "0")
        errors = []
        if not name:
            errors.append("Наименование товара не заполнено.")
        try:
            price = Decimal(price_str)
            if price <= 0:
                errors.append("Цена должна быть больше нуля.")
        except Exception:
            errors.append("Некорректная цена.")
            price = Decimal("0")
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append("Количество не может быть отрицательным.")
        except Exception:
            errors.append("Некорректное количество.")
            stock = 0
        if errors:
            return render(request, "sales/product_form.html", {"product": product, "errors": errors})
        product.name = name
        product.price = price
        product.stock = stock
        product.save()
        return redirect("product_list")
    return render(request, "sales/product_form.html", {"product": product})


def product_api(request):
    products = Product.objects.all()
    data = [
        {"id": p.id, "name": p.name, "price": str(p.price), "stock": p.stock}
        for p in products
    ]
    return JsonResponse(data, safe=False)


# ─── Orders ─────────────────────────────────────────────────────────

def order_create(request):
    clients = Client.objects.all()
    products = Product.objects.all()

    if request.method == "POST":
        client_id = request.POST.get("client_id")
        sale_type = request.POST.get("sale_type")
        items_json = request.POST.get("items_json", "[]")

        barter_items_json = request.POST.get("barter_items_json", "[]")

        client = get_object_or_404(Client, pk=client_id)
        items_data = json.loads(items_json)
        barter_items_data = json.loads(barter_items_json)

        warnings = []

        # Validate barter items
        if sale_type == "barter":
            if not barter_items_data:
                warnings.append("Для бартера необходимо указать товары в обмен.")
            else:
                barter_total = Decimal("0")
                for bi in barter_items_data:
                    if not bi.get("product_id"):
                        warnings.append("Есть незаполненные товары в обмене.")
                        break
                    bp = Product.objects.filter(pk=bi["product_id"]).first()
                    if bp:
                        barter_total += bp.price * int(bi.get("quantity", 0))
                items_total = Decimal("0")
                for item in items_data:
                    p = Product.objects.filter(pk=item.get("product_id")).first()
                    if p:
                        items_total += p.price * int(item.get("quantity", 0))
                if abs(items_total - barter_total) >= Decimal("0.01"):
                    warnings.append(f"Суммы не совпадают: отдано {items_total} руб., получено {barter_total} руб.")

        # Validate items
        for item in items_data:
            if not item.get("product_id"):
                warnings.append("Есть строки с незаполненным товаром.")
                break
            if Decimal(str(item.get("price", 0))) <= 0:
                warnings.append("Есть строки с нулевой ценой.")
                break
            if int(item.get("quantity", 0)) <= 0:
                warnings.append("Есть строки с нулевым количеством.")
                break

        # Calculate order total for credit/offset validation
        order_total = Decimal("0")
        for item in items_data:
            p = Product.objects.filter(pk=item.get("product_id")).first()
            if p:
                order_total += p.price * int(item.get("quantity", 0))

        # Credit validation: order total cannot exceed remaining credit
        if sale_type == "credit":
            effective_total = order_total - min(client.current_account, order_total)
            if effective_total > client.credit_remaining:
                warnings.append(
                    f"Сумма кредита ({effective_total} руб.) превышает остаток кредита "
                    f"({client.credit_remaining} руб.). Потолок кредита: {client.credit_limit} руб., "
                    f"текущий долг: {client.current_debt} руб."
                )
            if client.credit_limit > 0:
                future_debt = client.current_debt + effective_total
                if future_debt >= client.credit_limit * Decimal("0.9"):
                    warnings.append(
                        f"Внимание! После этого заказа долг клиента ({future_debt} руб.) "
                        f"достигнет {round(future_debt / client.credit_limit * 100, 1)}% от потолка кредита "
                        f"({client.credit_limit} руб.)."
                    )

        # Offset validation: cannot offset more than current debt
        if sale_type == "offset":
            if order_total > client.current_debt:
                warnings.append(
                    f"Сумма взаимозачёта ({order_total} руб.) превышает текущий долг клиента "
                    f"({client.current_debt} руб.). Нельзя зачесть больше, чем задолженность."
                )

        if warnings:
            has_hard_error = False
            for w in warnings:
                if "превышает остаток кредита" in w or "превышает текущий долг" in w or \
                   "Суммы не совпадают" in w or "незаполненным" in w or \
                   "нулевой ценой" in w or "нулевым количеством" in w or \
                   "незаполненным товаром" in w or "необходимо указать" in w:
                    has_hard_error = True
                    break
            if has_hard_error:
                return JsonResponse({"status": "error", "warnings": warnings})

        order = Order.objects.create(
            client=client, sale_type=sale_type, total_sum=0
        )

        total = Decimal("0")
        for item in items_data:
            product = get_object_or_404(Product, pk=item["product_id"])
            qty = int(item["quantity"])
            price = product.price
            line_total = price * qty

            OrderItem.objects.create(
                order=order, product=product, quantity=qty, price=price
            )
            total += line_total

            if sale_type in ("cash", "cashless", "credit", "barter"):
                product.stock -= qty
                product.save()
            elif sale_type == "offset":
                product.stock += qty
                product.save()

        order.total_sum = total
        order.save()

        # Update client accounts based on sale type
        if sale_type == "cash":
            client.total_purchases += total
        elif sale_type == "cashless":
            client.total_purchases += total
            client.current_account -= total
        elif sale_type == "credit":
            client.total_purchases += total
            if client.current_account > 0:
                account_use = min(client.current_account, total)
                client.current_account -= account_use
                remaining = total - account_use
            else:
                remaining = total
            client.current_debt += remaining
        elif sale_type == "barter":
            for bi in barter_items_data:
                barter_product = get_object_or_404(Product, pk=bi["product_id"])
                bqty = int(bi["quantity"])
                barter_product.stock += bqty
                barter_product.save()
        elif sale_type == "offset":
            client.current_debt -= total
        client.save()

        result = {
            "status": "ok",
            "order_id": order.pk,
            "debt_warning": client.debt_warning,
            "current_debt": str(client.current_debt),
            "credit_remaining": str(client.credit_remaining),
            "total_purchases": str(client.total_purchases),
            "current_account": str(client.current_account),
        }

        if sale_type == "credit" and client.debt_warning:
            result["credit_warning"] = (
                f"Внимание! Текущий долг клиента ({client.current_debt} руб.) составляет "
                f"{round(client.current_debt / client.credit_limit * 100, 1)}% от потолка кредита "
                f"({client.credit_limit} руб.)!"
            )

        if warnings:
            result["soft_warnings"] = warnings

        return JsonResponse(result)

    return render(
        request,
        "sales/order_create.html",
        {"clients": clients, "products": products},
    )


def order_list(request):
    orders = Order.objects.select_related("client").prefetch_related("items__product").all()
    return render(request, "sales/order_list.html", {"orders": orders})


def report(request):
    clients = Client.objects.all()
    report_data = []
    for client in clients:
        orders = Order.objects.filter(client=client)
        orders_info = []
        for order in orders:
            items = order.items.select_related("product").all()
            orders_info.append({"order": order, "items": items})
        report_data.append({
            "client": client,
            "orders": orders_info,
            "total": orders.aggregate(total=Sum("total_sum"))["total"] or 0,
        })
    return render(request, "sales/report.html", {"report_data": report_data})


# ════════════════════════════════════════════════════════════════════════════
# ЛАБ. №8 — ПЕЧАТНЫЕ ФОРМЫ (PDF)
# Аналог отчётов MS Access: заголовок, колонтитулы, область данных, итоги.
# Реализованы с помощью Python-библиотеки reportlab.
# ════════════════════════════════════════════════════════════════════════════

def _pdf_styles():
    """Возвращает набор стилей для PDF-документов (общий для всех форм)."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'RuTitle', fontName=_PDF_FONT, fontSize=16, alignment=TA_CENTER,
        spaceAfter=6, leading=20, textColor=colors.HexColor('#2c3e50'),
    ))
    styles.add(ParagraphStyle(
        'RuHeading', fontName=_PDF_FONT, fontSize=12, spaceAfter=4,
        textColor=colors.HexColor('#34495e'),
    ))
    styles.add(ParagraphStyle(
        'RuNormal', fontName=_PDF_FONT, fontSize=9, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        'RuSmall', fontName=_PDF_FONT, fontSize=8, textColor=colors.grey,
    ))
    styles.add(ParagraphStyle(
        'RuRight', fontName=_PDF_FONT, fontSize=9, alignment=TA_RIGHT,
    ))
    return styles


def _table_style_default():
    """Базовый стиль таблицы для печатных форм."""
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), _PDF_FONT),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('FONTNAME',      (0, 1), (-1, -1), _PDF_FONT),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])


def pdf_order(request, pk):
    """
    Лаб. №8: Печатная форма заказа (накладная).

    Структура по аналогии с отчётом MS Access:
      - Заголовок отчёта   — название и номер заказа;
      - Верхний колонтитул — дата и клиент;
      - Область данных     — позиции заказа (таблица);
      - Примечание отчёта  — итоговая сумма.
    """
    order = get_object_or_404(Order, pk=pk)
    items = order.items.select_related('product').all()
    styles = _pdf_styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    # ── Заголовок отчёта ──────────────────────────────────────────────────
    story.append(Paragraph('АРМ Оператора по продажам', styles['RuSmall']))
    story.append(Paragraph(f'Заказ №{order.pk}', styles['RuTitle']))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#667eea')))
    story.append(Spacer(1, 0.3*cm))

    # ── Верхний колонтитул — реквизиты ───────────────────────────────────
    meta = [
        ['Клиент:',   order.client.name,
         'Дата:',     order.created_at.strftime('%d.%m.%Y %H:%M')],
        ['Вид продажи:', order.get_sale_type_display(),
         'ИНН клиента:', order.client.inn or '—'],
    ]
    meta_table = Table(meta, colWidths=[3*cm, 7*cm, 3*cm, 4*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), _PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), _PDF_FONT),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#888888')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#888888')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Область данных — позиции заказа ──────────────────────────────────
    header = ['#', 'Наименование товара', 'Цена (руб.)', 'Кол-во', 'Сумма (руб.)']
    rows = [header]
    for i, item in enumerate(items, 1):
        rows.append([
            str(i),
            item.product.name,
            f'{item.price:,.2f}',
            str(item.quantity),
            f'{item.line_total:,.2f}',
        ])

    col_widths = [1*cm, 9*cm, 3*cm, 2*cm, 3*cm]
    data_table = Table(rows, colWidths=col_widths, repeatRows=1)
    ts = _table_style_default()
    ts.add('ALIGN', (0, 0), (0, -1), 'CENTER')
    ts.add('ALIGN', (2, 1), (-1, -1), 'RIGHT')
    data_table.setStyle(ts)
    story.append(data_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Примечание отчёта — итог ──────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
    total_row = Table(
        [['Итого:', f'{order.total_sum:,.2f} руб.']],
        colWidths=[14*cm, 3*cm],
    )
    total_row.setStyle(TableStyle([
        ('FONTNAME',   (0, 0), (-1, -1), _PDF_FONT),
        ('FONTSIZE',   (0, 0), (-1, -1), 11),
        ('FONTNAME',   (1, 0), (1, 0), _PDF_FONT),
        ('TEXTCOLOR',  (0, 0), (0, 0), colors.HexColor('#888888')),
        ('ALIGN',      (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(total_row)

    doc.build(story)
    buf.seek(0)
    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="order_{pk}.pdf"'
    return resp


def pdf_clients(request):
    """
    Лаб. №8: Печатная форма «Список клиентов» с кредитной информацией.
    Аналог отчёта MS Access с группировкой по должникам (90%+ от лимита).
    """
    clients = Client.objects.all().order_by('name')
    styles = _pdf_styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    story.append(Paragraph('АРМ Оператора по продажам', styles['RuSmall']))
    story.append(Paragraph('Список клиентов', styles['RuTitle']))
    story.append(Paragraph(
        f'Дата формирования: {__import__("datetime").date.today().strftime("%d.%m.%Y")}',
        styles['RuSmall']
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#667eea')))
    story.append(Spacer(1, 0.4*cm))

    header = ['#', 'Клиент', 'ИНН', 'Потолок кредита', 'Долг', 'Остаток', 'Покупки']
    rows = [header]
    for i, c in enumerate(clients, 1):
        warning = c.debt_warning
        rows.append([
            str(i),
            c.name,
            c.inn or '—',
            f'{c.credit_limit:,.0f}',
            f'{c.current_debt:,.0f}',
            f'{c.credit_remaining:,.0f}',
            f'{c.total_purchases:,.0f}',
        ])

    col_w = [0.8*cm, 5.5*cm, 2.5*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    ts = _table_style_default()
    ts.add('ALIGN', (3, 1), (-1, -1), 'RIGHT')
    # Красная подсветка для клиентов с долгом > 90%
    for i, c in enumerate(clients, 1):
        if c.debt_warning:
            ts.add('TEXTCOLOR', (4, i), (5, i), colors.HexColor('#e74c3c'))
    tbl.setStyle(ts)
    story.append(tbl)

    doc.build(story)
    buf.seek(0)
    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="clients.pdf"'
    return resp


def pdf_report(request):
    """
    Лаб. №8: Печатная форма сводного отчёта по продажам.
    Группировка по клиентам с суммами по видам продажи.
    """
    from django.db.models import Count
    clients = Client.objects.prefetch_related('orders').all().order_by('name')
    styles = _pdf_styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    story.append(Paragraph('АРМ Оператора по продажам', styles['RuSmall']))
    story.append(Paragraph('Сводный отчёт по продажам', styles['RuTitle']))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#667eea')))
    story.append(Spacer(1, 0.4*cm))

    sale_types = [
        ('cash', 'Наличные'), ('cashless', 'Безнал'),
        ('credit', 'Кредит'), ('barter', 'Бартер'), ('offset', 'Взаимозачёт'),
    ]
    header = ['Клиент'] + [st[1] for st in sale_types] + ['Итого']
    rows = [header]
    grand_total = Decimal('0')

    for c in clients:
        row = [c.name]
        client_total = Decimal('0')
        for stype, _ in sale_types:
            s = c.orders.filter(sale_type=stype).aggregate(t=Sum('total_sum'))['t'] or Decimal('0')
            row.append(f'{s:,.0f}' if s else '—')
            client_total += s
        row.append(f'{client_total:,.0f}')
        grand_total += client_total
        rows.append(row)

    # Строка итогов
    rows.append(['ИТОГО:'] + [''] * len(sale_types) + [f'{grand_total:,.0f}'])

    col_w = [4.5*cm] + [2.2*cm] * len(sale_types) + [2.5*cm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    ts = _table_style_default()
    ts.add('ALIGN', (1, 1), (-1, -1), 'RIGHT')
    # Выделяем итоговую строку
    ts.add('BACKGROUND', (0, len(rows)-1), (-1, len(rows)-1), colors.HexColor('#667eea'))
    ts.add('TEXTCOLOR',  (0, len(rows)-1), (-1, len(rows)-1), colors.white)
    ts.add('FONTNAME',   (0, len(rows)-1), (-1, len(rows)-1), _PDF_FONT)
    tbl.setStyle(ts)
    story.append(tbl)

    doc.build(story)
    buf.seek(0)
    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="sales_report.pdf"'
    return resp
