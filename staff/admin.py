"""Регистрация моделей staff в панели администратора."""

from django.contrib import admin
from django.contrib.auth.models import Group, User
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name_patronymic', 'position',
                    'work_phone', 'personal_phone']
    list_filter = ['position']
    search_fields = ['last_name', 'first_name_patronymic', 'position']
    readonly_fields = ['created_at', 'updated_at']
