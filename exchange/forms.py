"""
Формы для приложения exchange (Лаб. №3).
"""

from django import forms
from .models import SalesRecord


class SalesRecordForm(forms.ModelForm):
    """
    Форма добавления/редактирования записи продажи.
    Все поля с русскими подписями согласно заданию.
    """

    class Meta:
        model = SalesRecord
        fields = ['product_name', 'product_group', 'quantity',
                  'selling_price', 'purchase_price', 'discount']
        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Например: Молоко 1л'
            }),
            'product_group': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Например: Молочные продукты'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0.01'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'
            }),
        }
        labels = {
            'product_name': 'Наименование товара',
            'product_group': 'Группа товара',
            'quantity': 'Количество',
            'selling_price': 'Цена продажи (руб.)',
            'purchase_price': 'Цена закупки (руб.)',
            'discount': 'Скидка (%)',
        }

    def clean_discount(self):
        """Проверка: скидка от 0 до 100%."""
        d = self.cleaned_data['discount']
        if d < 0 or d > 100:
            raise forms.ValidationError('Скидка должна быть от 0 до 100%.')
        return d

    def clean(self):
        """Проверка: цена закупки не должна превышать цену продажи."""
        cleaned = super().clean()
        sp = cleaned.get('selling_price')
        pp = cleaned.get('purchase_price')
        if sp is not None and pp is not None and pp > sp:
            self.add_error('purchase_price', 'Цена закупки не может превышать цену продажи.')
        return cleaned
