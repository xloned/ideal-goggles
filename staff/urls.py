"""URL-маршруты для Лаб. №4 (доступ) и №5 (курсы валют)."""

from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Аутентификация
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Список сотрудников (доступен всем, в т.ч. гостям)
    path('', views.employee_list, name='employee_list'),

    # Управление сотрудниками (права по роли)
    path('add/', views.employee_add, name='employee_add'),
    path('<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    # Лаб. №5 — Курсы валют ЦБ РФ
    path('currency/', views.currency_rates, name='currency_rates'),
]
