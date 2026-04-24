"""
Лабораторная работа №4 — Распределённая работа пользователей.
Разграничение доступа: 4 роли — Директор, Заместитель, Секретарь, Гость.

Модель сотрудника с персональными данными.
Контроль доступа реализован через Django-группы и кастомный middleware.
"""

from django.db import models


class Employee(models.Model):
    """
    Сотрудник фирмы.
    Поля согласно заданию лаб. работы №4:
      last_name           — фамилия;
      first_name_patronymic — имя и отчество (одно поле);
      position            — должность;
      address             — адрес (скрыт от роли «Гость»);
      personal_phone      — личный телефон (скрыт от роли «Гость»);
      work_phone          — рабочий телефон (виден «Гостю»).
    """

    last_name = models.CharField('Фамилия', max_length=100)
    first_name_patronymic = models.CharField('Имя и отчество', max_length=200)
    position = models.CharField('Должность', max_length=150)
    address = models.CharField('Адрес', max_length=300)
    personal_phone = models.CharField('Личный телефон', max_length=20)
    work_phone = models.CharField('Рабочий телефон', max_length=20)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name_patronymic']

    def __str__(self):
        return f'{self.last_name} {self.first_name_patronymic}'

    @property
    def full_name(self):
        """Полное имя: фамилия + имя и отчество."""
        return f'{self.last_name} {self.first_name_patronymic}'
