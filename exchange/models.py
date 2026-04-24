"""
Лабораторная работа №3 — Обмен данными между программами.
Вариант 6: Продажи товаров через кассовый аппарат.

Модели для программы-источника (ввод данных о продажах).
Обработка: расчёт прибыли по группам товаров.
Визуализация: matplotlib-диаграмма прибыли по группам.
"""

from django.db import models
from decimal import Decimal


class SalesRecord(models.Model):
    """
    Запись о продаже товара — один элемент кассового чека.
    Поля соответствуют варианту 6 задания:
      product_name   — наименование товара;
      product_group  — группа товара;
      quantity       — проданное количество;
      selling_price  — продажная цена (без скидки);
      purchase_price — закупочная цена;
      discount       — скидка в процентах (0–100).
    """

    product_name = models.CharField('Наименование товара', max_length=200)
    product_group = models.CharField('Группа товара', max_length=100)
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2)
    selling_price = models.DecimalField('Цена продажи', max_digits=12, decimal_places=2)
    purchase_price = models.DecimalField('Цена закупки', max_digits=12, decimal_places=2)
    discount = models.DecimalField('Скидка (%)', max_digits=5, decimal_places=2, default=Decimal('0'))
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    exported = models.BooleanField('Выгружен', default=False)

    class Meta:
        verbose_name = 'Запись продажи'
        verbose_name_plural = 'Записи продаж'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product_name} ({self.product_group}) — {self.quantity} шт.'

    @property
    def revenue(self):
        """Выручка: цена продажи * количество (без учёта скидки)."""
        return self.selling_price * self.quantity

    @property
    def revenue_with_discount(self):
        """Выручка с учётом скидки."""
        factor = Decimal('1') - self.discount / Decimal('100')
        return self.selling_price * self.quantity * factor

    @property
    def cost(self):
        """Себестоимость: цена закупки * количество."""
        return self.purchase_price * self.quantity

    @property
    def profit(self):
        """
        Прибыль одной продажи = цена продажи без скидки * количество − цена закупки * количество.
        Формула согласно заданию.
        """
        return self.revenue - self.cost
