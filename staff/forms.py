"""
Формы для приложения staff (Лаб. №4).
"""

from django import forms
from .models import Employee


class LoginForm(forms.Form):
    """Форма входа в систему."""

    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя пользователя',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
        })
    )


class EmployeeForm(forms.ModelForm):
    """Форма добавления/редактирования сотрудника."""

    class Meta:
        model = Employee
        fields = ['last_name', 'first_name_patronymic', 'position',
                  'address', 'personal_phone', 'work_phone']
        widgets = {
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Иванов'
            }),
            'first_name_patronymic': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Иван Иванович'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Менеджер'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'г. Москва, ул. Пушкина, д. 1'
            }),
            'personal_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '+7 (999) 000-00-00'
            }),
            'work_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '+7 (499) 000-00-00'
            }),
        }
        labels = {
            'last_name': 'Фамилия',
            'first_name_patronymic': 'Имя и отчество',
            'position': 'Должность',
            'address': 'Адрес',
            'personal_phone': 'Личный телефон',
            'work_phone': 'Рабочий телефон',
        }
