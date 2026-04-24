"""
Лабораторная работа №9 — Добавление новых информационных объектов.
Учёт пробега автотранспорта.

Три объекта согласно заданию:
  Automobile — справочник «Автомобили»;
  Driver     — справочник «Водители» (связан с сотрудниками Лаб. №4);
  Waybill    — документ «Путевой лист» с вычисляемыми полями.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Automobile(models.Model):
    """
    Справочник «Автомобили».
    Поля согласно заданию Лаб. №9:
      make         — марка автомобиля;
      state_number — государственный регистрационный номер;
      year         — год выпуска;
      fuel_norm    — норма расхода топлива (литров на 1 км).
    """

    make = models.CharField(
        "Марка автомобиля",
        max_length=100,
        help_text="Например: Toyota Camry, LADA Vesta",
    )
    state_number = models.CharField(
        "Гос. номер",
        max_length=20,
        unique=True,
        help_text="Например: А123БВ777",
    )
    year = models.PositiveIntegerField(
        "Год выпуска",
        validators=[MinValueValidator(1900)],
    )
    fuel_norm = models.DecimalField(
        "Норма расхода (л/км)",
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Средний расход топлива в литрах на 1 км",
    )

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"
        ordering = ["make", "state_number"]

    def __str__(self):
        return f"{self.make} ({self.state_number})"


class Driver(models.Model):
    """
    Справочник «Водители».
    Связывает сотрудника (из Лаб. №4) с закреплённым автомобилем.
    Поля согласно заданию:
      employee   — ссылка на справочник «Сотрудники» (staff.Employee);
      automobile — ссылка на справочник «Автомобили».
    """

    employee = models.OneToOneField(
        "staff.Employee",
        on_delete=models.CASCADE,
        verbose_name="Сотрудник",
        related_name="driver_profile",
    )
    automobile = models.ForeignKey(
        Automobile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Закреплённый автомобиль",
        related_name="drivers",
    )

    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"
        ordering = ["employee__last_name"]

    def __str__(self):
        return f"{self.employee.full_name}"

    @property
    def automobile_display(self):
        """Отображение автомобиля или «не назначен»."""
        return str(self.automobile) if self.automobile else "Не назначен"


class Waybill(models.Model):
    """
    Документ «Путевой лист».
    Поля согласно заданию Лаб. №9:
      driver           — водитель (из справочника «Водители»);
      automobile       — автомобиль (заполняется автоматически по водителю);
      departure_time   — время выезда (вводится);
      arrival_time     — время заезда (вводится);
      start_mileage    — начальный километраж (вводится);
      end_mileage      — конечный километраж (вводится);
      mileage          — пробег (вычисляется: конечный − начальный);
      fuel_consumption — расход топлива (вычисляется: пробег × норма расхода).

    Вычисляемые поля реализованы как Python-свойства и сохраняются в БД
    для удобства поиска и отчётности.
    """

    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        verbose_name="Водитель",
        related_name="waybills",
    )
    automobile = models.ForeignKey(
        Automobile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Автомобиль",
        related_name="waybills",
    )
    departure_time = models.DateTimeField("Время выезда")
    arrival_time = models.DateTimeField("Время заезда", null=True, blank=True)
    start_mileage = models.DecimalField(
        "Начальный километраж (км)",
        max_digits=10,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0"))],
    )
    end_mileage = models.DecimalField(
        "Конечный километраж (км)",
        max_digits=10,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    # Вычисляемые поля (хранятся в БД для отчётов)
    mileage = models.DecimalField(
        "Пробег (км)",
        max_digits=10,
        decimal_places=1,
        default=Decimal("0"),
        editable=False,
    )
    fuel_consumption = models.DecimalField(
        "Расход топлива (л)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        editable=False,
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Путевой лист"
        verbose_name_plural = "Путевые листы"
        ordering = ["-departure_time"]

    def __str__(self):
        return f"Путевой лист №{self.pk} — {self.driver} — {self.departure_time:%d.%m.%Y}"

    def compute_fields(self):
        """
        Вычисляет пробег и расход топлива.
        Пробег = конечный километраж − начальный километраж.
        Расход = пробег × норма расхода топлива автомобиля.
        """
        if self.end_mileage and self.end_mileage > self.start_mileage:
            self.mileage = self.end_mileage - self.start_mileage
            if self.automobile and self.automobile.fuel_norm:
                self.fuel_consumption = self.mileage * self.automobile.fuel_norm
        else:
            self.mileage = Decimal("0")
            self.fuel_consumption = Decimal("0")

    def save(self, *args, **kwargs):
        """При сохранении подставляем автомобиль водителя и пересчитываем поля."""
        if self.driver and not self.automobile:
            self.automobile = self.driver.automobile
        self.compute_fields()
        super().save(*args, **kwargs)

    @property
    def is_closed(self):
        """Путевой лист закрыт, если указан конечный километраж."""
        return self.end_mileage is not None
