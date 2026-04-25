"""URL-маршруты Лаб 10 — Бухгалтерские отчёты."""

from django.urls import path
from . import views

app_name = 'lab10'

urlpatterns = [
    path('', views.index, name='index'),

    # Отчёт 1: Остатки товаров
    path('stock/',     views.report_stock,     name='stock'),
    path('stock/pdf/', views.report_stock_pdf, name='stock_pdf'),

    # Отчёт 2: Подотчётники
    path('advances/',            views.report_advances,     name='advances'),
    path('advances/pdf/',        views.report_advances_pdf, name='advances_pdf'),
    path('advances/add/',        views.advance_add,         name='advance_add'),
    path('advances/delete/<int:pk>/', views.advance_delete, name='advance_delete'),

    # Отчёт 3: Издержки организации
    path('expenses/',             views.report_expenses,     name='expenses'),
    path('expenses/pdf/',         views.report_expenses_pdf, name='expenses_pdf'),
    path('expenses/add/',         views.expense_add,         name='expense_add'),
    path('expenses/delete/<int:pk>/', views.expense_delete,  name='expense_delete'),
    path('expenses/category/add/', views.category_add,       name='category_add'),
]
