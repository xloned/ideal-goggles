"""Регистрация моделей exchange в панели администратора."""

from django.contrib import admin
from .models import SalesRecord


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'product_group', 'quantity',
                    'selling_price', 'purchase_price', 'discount',
                    'profit_display', 'exported', 'created_at']
    list_filter = ['product_group', 'exported']
    search_fields = ['product_name', 'product_group']
    readonly_fields = ['created_at', 'exported']

    @admin.display(description='Прибыль (₽)')
    def profit_display(self, obj):
        return f'{obj.profit:,.2f}'
