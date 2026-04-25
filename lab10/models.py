"""
Лабораторная работа №10 — Создание дополнительных бухгалтерских отчётов.

Аналог «конструктора бухгалтерских запросов 1С Предприятие 7.7».
Python/Django — замена системы 1С.

Три варианта отчётов:
  1. «Остатки товаров»   — перечень товаров с количеством и стоимостью (данные из sales.Product)
  2. «Подотчётники»      — список сотрудников с суммами под отчёт
  3. «Издержки организации» — список статей издержек за период
"""

from django.db import models
from staff.models import Employee


class ExpenseAdvance(models.Model):
    """
    Подотчётная сумма — деньги, выданные сотруднику под отчёт.
    Используется в отчёте «Подотчётники».
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='advances',
        verbose_name='Сотрудник',
    )
    amount = models.DecimalField('Сумма (руб.)', max_digits=12, decimal_places=2)
    issued_date = models.DateField('Дата выдачи')
    description = models.CharField('Назначение', max_length=300, blank=True)
    returned = models.BooleanField('Возвращено', default=False)

    class Meta:
        verbose_name = 'Подотчётная сумма'
        verbose_name_plural = 'Подотчётные суммы'
        ordering = ['-issued_date']

    def __str__(self):
        return f'{self.employee} — {self.amount} руб. ({self.issued_date})'


class ExpenseCategory(models.Model):
    """Статья издержек организации."""
    name = models.CharField('Наименование статьи', max_length=200, unique=True)

    class Meta:
        verbose_name = 'Статья издержек'
        verbose_name_plural = 'Статьи издержек'
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    Издержка организации — запись о расходе по конкретной статье.
    Используется в отчёте «Издержки организации».
    """
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Статья',
    )
    amount = models.DecimalField('Сумма (руб.)', max_digits=12, decimal_places=2)
    expense_date = models.DateField('Дата')
    description = models.CharField('Описание', max_length=300, blank=True)

    class Meta:
        verbose_name = 'Издержка'
        verbose_name_plural = 'Издержки'
        ordering = ['-expense_date']

    def __str__(self):
        return f'{self.category} — {self.amount} руб. ({self.expense_date})'
