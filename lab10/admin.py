from django.contrib import admin
from .models import ExpenseAdvance, ExpenseCategory, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount', 'expense_date', 'description']
    list_filter  = ['category', 'expense_date']


@admin.register(ExpenseAdvance)
class ExpenseAdvanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'amount', 'issued_date', 'returned', 'description']
    list_filter  = ['returned', 'issued_date']
