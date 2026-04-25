"""
Лабораторная работа №10 — Дополнительные бухгалтерские отчёты.

Три отчёта (аналог конструктора бухгалтерских запросов 1С Предприятие 7.7):
  1. «Остатки товаров»      — quantity + cost per product, total.
  2. «Подотчётники»         — advances per employee for a given date, total.
  3. «Издержки организации» — expenses by category for a date range, total.

Каждый отчёт доступен в двух форматах: HTML (экран) и PDF (reportlab).
"""

import io
from decimal import Decimal
from datetime import date

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Count

# reportlab — PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from sales.models import Product
from .models import ExpenseAdvance, Expense, ExpenseCategory

# ──────────────────────────────────────────────────
# PDF helpers
# ──────────────────────────────────────────────────
_PDF_FONT = 'Helvetica'
try:
    import os
    font_candidates = [
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/Library/Fonts/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    ]
    for _fp in font_candidates:
        if os.path.exists(_fp):
            pdfmetrics.registerFont(TTFont('ReportFont', _fp))
            _PDF_FONT = 'ReportFont'
            break
except Exception:
    pass


def _pdf_styles():
    styles = getSampleStyleSheet()
    base = {'fontName': _PDF_FONT}
    return {
        'title': ParagraphStyle('T', **base, fontSize=16, spaceAfter=6, leading=20, alignment=1),
        'subtitle': ParagraphStyle('S', **base, fontSize=11, spaceAfter=10, textColor=colors.grey, alignment=1),
        'normal': ParagraphStyle('N', **base, fontSize=10, spaceAfter=4),
        'footer': ParagraphStyle('F', **base, fontSize=8, textColor=colors.grey, alignment=1),
    }


def _table_style(header_color=colors.HexColor('#2c3e50')):
    return TableStyle([
        ('FONTNAME',      (0, 0), (-1, -1), _PDF_FONT),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('BACKGROUND',    (0, 0), (-1, 0),  header_color),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  _PDF_FONT),
        ('FONTSIZE',      (0, 0), (-1, 0),  10),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
        ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#d5e8f0')),
        ('FONTNAME',      (0, -1), (-1, -1), _PDF_FONT),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ALIGN',         (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
    ])


def _build_pdf(title_text: str, subtitle_text: str, story_items: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    st = _pdf_styles()
    story = [
        Paragraph(title_text, st['title']),
        HRFlowable(width='100%', thickness=2, color=colors.HexColor('#2c3e50'), spaceAfter=6),
        Paragraph(subtitle_text, st['subtitle']),
        Spacer(1, 0.3*cm),
    ]
    story.extend(story_items)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f'Сформировано: {date.today().strftime("%d.%m.%Y")} · Лабораторная работа №10',
        st['footer'],
    ))
    doc.build(story)
    return buf.getvalue()


# ──────────────────────────────────────────────────
# INDEX
# ──────────────────────────────────────────────────

def index(request):
    """Главная страница Лаб 10 — список доступных отчётов."""
    return render(request, 'lab10/index.html')


# ──────────────────────────────────────────────────
# Отчёт 1: Остатки товаров
# ──────────────────────────────────────────────────

def report_stock(request):
    """
    Отчёт «Остатки товаров».
    Перечень товаров с общим количеством и стоимостью. Выводит общую сумму.
    Аналог варианта 1 из задания Лаб 10.
    """
    products = Product.objects.order_by('name')
    rows = []
    total_qty = 0
    total_cost = Decimal('0')
    for p in products:
        cost = p.price * p.stock
        rows.append({
            'name': p.name,
            'price': p.price,
            'stock': p.stock,
            'cost': cost,
        })
        total_qty += p.stock
        total_cost += cost

    return render(request, 'lab10/report_stock.html', {
        'rows': rows,
        'total_qty': total_qty,
        'total_cost': total_cost,
        'report_date': date.today(),
    })


def report_stock_pdf(request):
    """PDF-версия отчёта «Остатки товаров»."""
    products = Product.objects.order_by('name')
    table_data = [['№', 'Наименование товара', 'Цена (руб.)', 'Кол-во', 'Стоимость (руб.)']]
    total_qty  = 0
    total_cost = Decimal('0')
    for i, p in enumerate(products, 1):
        cost = p.price * p.stock
        table_data.append([
            str(i), p.name,
            f'{p.price:,.2f}',
            str(p.stock),
            f'{cost:,.2f}',
        ])
        total_qty += p.stock
        total_cost += cost

    table_data.append(['', 'ИТОГО', '', str(total_qty), f'{total_cost:,.2f}'])

    w = 17 * cm
    col_widths = [1*cm, 7*cm, 3*cm, 2.5*cm, 3.5*cm]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_table_style())

    pdf = _build_pdf(
        'Отчёт: Остатки товаров',
        f'Данные на {date.today().strftime("%d.%m.%Y")} · Всего позиций: {len(products)}',
        [tbl],
    )
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="stock_report.pdf"'
    return resp


# ──────────────────────────────────────────────────
# Отчёт 2: Подотчётники
# ──────────────────────────────────────────────────

def report_advances(request):
    """
    Отчёт «Подотчётники».
    Список сотрудников с суммами, выданными под отчёт на указанную дату.
    Аналог варианта 2 из задания Лаб 10.
    """
    report_date = request.GET.get('date', str(date.today()))
    try:
        report_date_obj = date.fromisoformat(report_date)
    except ValueError:
        report_date_obj = date.today()
        report_date = str(report_date_obj)

    # Суммы по каждому сотруднику, выданные не позже указанной даты и ещё не возвращённые
    qs = (
        ExpenseAdvance.objects
        .filter(issued_date__lte=report_date_obj, returned=False)
        .values('employee__id', 'employee__last_name', 'employee__first_name_patronymic',
                'employee__position')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('employee__last_name')
    )
    total_sum = sum(r['total'] for r in qs)

    return render(request, 'lab10/report_advances.html', {
        'rows': qs,
        'total_sum': total_sum,
        'report_date': report_date,
        'advances_all': ExpenseAdvance.objects.select_related('employee').order_by('-issued_date'),
    })


def report_advances_pdf(request):
    """PDF-версия отчёта «Подотчётники»."""
    report_date = request.GET.get('date', str(date.today()))
    try:
        report_date_obj = date.fromisoformat(report_date)
    except ValueError:
        report_date_obj = date.today()

    qs = (
        ExpenseAdvance.objects
        .filter(issued_date__lte=report_date_obj, returned=False)
        .values('employee__last_name', 'employee__first_name_patronymic',
                'employee__position')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('employee__last_name')
    )
    total_sum = sum(r['total'] for r in qs)

    table_data = [['№', 'Сотрудник', 'Должность', 'Кол-во выдач', 'Сумма (руб.)']]
    for i, r in enumerate(qs, 1):
        fio = f'{r["employee__last_name"]} {r["employee__first_name_patronymic"]}'
        table_data.append([
            str(i), fio, r['employee__position'],
            str(r['count']),
            f'{r["total"]:,.2f}',
        ])
    table_data.append(['', 'ИТОГО', '', '', f'{total_sum:,.2f}'])

    col_widths = [1*cm, 6*cm, 4*cm, 2.5*cm, 3.5*cm]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_table_style(header_color=colors.HexColor('#1a5276')))

    pdf = _build_pdf(
        'Отчёт: Подотчётники',
        f'На дату {report_date_obj.strftime("%d.%m.%Y")} · Сотрудников: {qs.count()}',
        [tbl],
    )
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="advances_report.pdf"'
    return resp


# ──────────────────────────────────────────────────
# Отчёт 3: Издержки организации
# ──────────────────────────────────────────────────

def report_expenses(request):
    """
    Отчёт «Издержки организации».
    Список статей издержек с суммами за выбранный период.
    Аналог варианта 3 из задания Лаб 10.
    """
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', str(date.today()))

    qs = Expense.objects.all()
    if date_from:
        qs = qs.filter(expense_date__gte=date_from)
    if date_to:
        qs = qs.filter(expense_date__lte=date_to)

    # Агрегация по статьям
    by_category = (
        qs.values('category__name')
          .annotate(total=Sum('amount'), count=Count('id'))
          .order_by('category__name')
    )
    total_sum = sum(r['total'] for r in by_category)

    return render(request, 'lab10/report_expenses.html', {
        'rows': by_category,
        'total_sum': total_sum,
        'date_from': date_from,
        'date_to': date_to,
        'expenses_all': Expense.objects.select_related('category').order_by('-expense_date'),
        'categories': ExpenseCategory.objects.all(),
    })


def report_expenses_pdf(request):
    """PDF-версия отчёта «Издержки организации»."""
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', str(date.today()))

    qs = Expense.objects.all()
    if date_from:
        qs = qs.filter(expense_date__gte=date_from)
    if date_to:
        qs = qs.filter(expense_date__lte=date_to)

    by_category = (
        qs.values('category__name')
          .annotate(total=Sum('amount'), count=Count('id'))
          .order_by('category__name')
    )
    total_sum = sum(r['total'] for r in by_category)

    period_str = ''
    if date_from:
        period_str += f'с {date_from} '
    period_str += f'по {date_to}'

    table_data = [['№', 'Статья издержек', 'Кол-во операций', 'Сумма (руб.)']]
    for i, r in enumerate(by_category, 1):
        table_data.append([
            str(i),
            r['category__name'],
            str(r['count']),
            f'{r["total"]:,.2f}',
        ])
    table_data.append(['', 'ИТОГО', '', f'{total_sum:,.2f}'])

    col_widths = [1*cm, 8*cm, 3.5*cm, 4.5*cm]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_table_style(header_color=colors.HexColor('#1e8449')))

    pdf = _build_pdf(
        'Отчёт: Издержки организации',
        f'Период: {period_str}',
        [tbl],
    )
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="expenses_report.pdf"'
    return resp


# ──────────────────────────────────────────────────
# CRUD для тестовых данных (подотчётники и издержки)
# ──────────────────────────────────────────────────

def advance_add(request):
    """Добавить запись о выдаче под отчёт."""
    from staff.models import Employee as Emp
    if request.method == 'POST':
        emp_id  = request.POST.get('employee')
        amount  = request.POST.get('amount', '0')
        dt      = request.POST.get('issued_date', str(date.today()))
        desc    = request.POST.get('description', '')
        try:
            emp = Emp.objects.get(pk=emp_id)
            ExpenseAdvance.objects.create(
                employee=emp,
                amount=Decimal(amount),
                issued_date=dt,
                description=desc,
            )
        except Exception:
            pass
    return _redirect_back(request, 'lab10:advances')


def advance_delete(request, pk):
    ExpenseAdvance.objects.filter(pk=pk).delete()
    return _redirect_back(request, 'lab10:advances')


def expense_add(request):
    """Добавить запись издержки."""
    if request.method == 'POST':
        cat_id = request.POST.get('category')
        amount = request.POST.get('amount', '0')
        dt     = request.POST.get('expense_date', str(date.today()))
        desc   = request.POST.get('description', '')
        try:
            cat = ExpenseCategory.objects.get(pk=cat_id)
            Expense.objects.create(
                category=cat,
                amount=Decimal(amount),
                expense_date=dt,
                description=desc,
            )
        except Exception:
            pass
    return _redirect_back(request, 'lab10:expenses')


def expense_delete(request, pk):
    Expense.objects.filter(pk=pk).delete()
    return _redirect_back(request, 'lab10:expenses')


def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            ExpenseCategory.objects.get_or_create(name=name)
    return _redirect_back(request, 'lab10:expenses')


def _redirect_back(request, fallback_name):
    from django.shortcuts import redirect
    referer = request.META.get('HTTP_REFERER', '')
    if referer:
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(referer)
    from django.urls import reverse
    return redirect(reverse(fallback_name))
