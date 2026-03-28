from django.db import models


class SensorConfig(models.Model):
    """Конфигурация параметра мониторинга"""
    name = models.CharField("Название параметра", max_length=200, default="Температура")
    unit = models.CharField("Единица измерения", max_length=50, default="°C")
    min_value = models.FloatField("Минимум допустимого диапазона", default=10.0)
    max_value = models.FloatField("Максимум допустимого диапазона", default=40.0)
    warning_percent = models.FloatField("Порог предупреждения (%)", default=15.0)
    history_count = models.IntegerField("Количество предыдущих значений (N1)", default=10)

    class Meta:
        verbose_name = "Конфигурация датчика"

    def __str__(self):
        return self.name


class SensorReading(models.Model):
    """Показание датчика"""
    config = models.ForeignKey(SensorConfig, on_delete=models.CASCADE, related_name="readings")
    value = models.FloatField("Значение")
    timestamp = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Показание"
        verbose_name_plural = "Показания"

    def __str__(self):
        return f"{self.value} {self.config.unit} @ {self.timestamp:%H:%M:%S}"
