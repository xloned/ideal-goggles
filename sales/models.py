"""
Модели информационной системы АРМ Оператора по продажам.
Лабораторная работа №1 — подсистема ручного ввода данных.
Лабораторная работа №7 — модификация: добавлено поле ИНН с валидацией.
"""

from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal


def validate_inn(value: str) -> None:
    """
    Лаб. №7: Валидация ИНН по алгоритму ФНС России.

    ИНН организации — 10 цифр, физ. лица — 12 цифр.
    Пустое значение допустимо (поле необязательное).
    Алгоритм проверки контрольных цифр задокументирован на сайте ФНС.
    """
    if not value:           # пустое значение — разрешено
        return
    if not value.isdigit():
        raise ValidationError('ИНН должен содержать только цифры.')
    n = len(value)
    if n not in (10, 12):
        raise ValidationError('ИНН должен содержать 10 (организация) или 12 (физ. лицо) цифр.')

    digits = [int(c) for c in value]

    def _check(weights, pos):
        """Считает контрольную цифру по весовым коэффициентам."""
        s = sum(w * d for w, d in zip(weights, digits)) % 11
        return (s % 10) == digits[pos]

    if n == 10:
        ok = _check([2, 4, 10, 3, 5, 9, 4, 6, 8], 9)
    else:   # 12 цифр
        ok = (_check([7, 2, 4, 10, 3, 5, 9, 4, 6, 8], 10) and
              _check([3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8], 11))

    if not ok:
        raise ValidationError('ИНН содержит ошибку в контрольных цифрах.')


class Client(models.Model):
    name = models.CharField("Имя клиента", max_length=200)
    # ── Лаб. №7: новое поле «ИНН» ──────────────────────────────────────────
    inn = models.CharField(
        "ИНН",
        max_length=12,
        blank=True,
        default="",
        validators=[validate_inn],
        help_text="10 цифр (организация) или 12 цифр (физ. лицо). Необязательно.",
    )
    # ────────────────────────────────────────────────────────────────────────
    total_purchases = models.DecimalField(
        "Общий счёт покупок", max_digits=12, decimal_places=2, default=0
    )
    current_account = models.DecimalField(
        "Текущий счёт", max_digits=12, decimal_places=2, default=0
    )
    credit_limit = models.DecimalField(
        "Потолок кредита", max_digits=12, decimal_places=2, default=0
    )
    current_debt = models.DecimalField(
        "Текущий долг", max_digits=12, decimal_places=2, default=0
    )
    comment = models.TextField("Комментарий", blank=True, default="")

    @property
    def credit_remaining(self):
        return self.credit_limit - self.current_debt

    @property
    def debt_warning(self):
        if self.credit_limit > 0:
            return self.current_debt >= self.credit_limit * Decimal("0.9")
        return False

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("Наименование товара", max_length=200)
    price = models.DecimalField("Цена", max_digits=12, decimal_places=2)
    stock = models.IntegerField("Остаток на складе", default=0)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.price} руб.)"


class Order(models.Model):
    SALE_TYPE_CHOICES = [
        ("cash", "Наличный расчёт"),
        ("cashless", "Безналичный расчёт"),
        ("credit", "Кредит"),
        ("barter", "Бартер"),
        ("offset", "Взаимозачёт"),
    ]

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="orders", verbose_name="Клиент"
    )
    sale_type = models.CharField(
        "Вид продажи", max_length=20, choices=SALE_TYPE_CHOICES
    )
    total_sum = models.DecimalField(
        "Общая сумма", max_digits=12, decimal_places=2, default=0
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.pk} — {self.client.name} ({self.get_sale_type_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Товар"
    )
    quantity = models.IntegerField("Количество", default=1)
    price = models.DecimalField("Цена за единицу", max_digits=12, decimal_places=2)

    @property
    def line_total(self):
        return self.price * self.quantity

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
