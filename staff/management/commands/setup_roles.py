"""
Management-команда для настройки ролей (групп) и тестовых пользователей.
Запуск: python manage.py setup_roles

Создаёт 4 группы согласно Лаб. №4:
  - director  (Директор)
  - deputy    (Заместитель директора)
  - secretary (Секретарь)
  (Гость — не требует аккаунта, просматривает без авторизации)

Создаёт тестовых пользователей:
  - director / director123
  - deputy / deputy123
  - secretary / secretary123
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from staff.models import Employee


class Command(BaseCommand):
    help = 'Создаёт группы ролей и тестовых пользователей для Лаб. №4'

    def handle(self, *args, **options):
        # ── Создание групп ───────────────────────────────────────
        roles = ['director', 'deputy', 'secretary']
        for role_name in roles:
            group, created = Group.objects.get_or_create(name=role_name)
            status = 'создана' if created else 'уже существует'
            self.stdout.write(f'  Группа «{role_name}» — {status}')

        # ── Создание тестовых пользователей ──────────────────────
        test_users = [
            {'username': 'director',  'password': 'director123',  'role': 'director'},
            {'username': 'deputy',    'password': 'deputy123',    'role': 'deputy'},
            {'username': 'secretary', 'password': 'secretary123', 'role': 'secretary'},
        ]
        for u in test_users:
            user, created = User.objects.get_or_create(username=u['username'])
            if created:
                user.set_password(u['password'])
                user.save()
            group = Group.objects.get(name=u['role'])
            user.groups.set([group])
            status = 'создан' if created else 'обновлён'
            self.stdout.write(f'  Пользователь «{u["username"]}» ({u["password"]}) — {status}')

        # ── Создание тестовых сотрудников ────────────────────────
        sample_employees = [
            {
                'last_name': 'Иванов',
                'first_name_patronymic': 'Иван Иванович',
                'position': 'Директор',
                'address': 'г. Москва, ул. Тверская, д. 1',
                'personal_phone': '+7 (999) 111-11-11',
                'work_phone': '+7 (499) 111-11-11',
            },
            {
                'last_name': 'Петрова',
                'first_name_patronymic': 'Мария Сергеевна',
                'position': 'Заместитель директора',
                'address': 'г. Москва, ул. Арбат, д. 10, кв. 5',
                'personal_phone': '+7 (999) 222-22-22',
                'work_phone': '+7 (499) 222-22-22',
            },
            {
                'last_name': 'Сидоров',
                'first_name_patronymic': 'Алексей Петрович',
                'position': 'Главный бухгалтер',
                'address': 'г. Москва, ул. Ленина, д. 15, кв. 3',
                'personal_phone': '+7 (999) 333-33-33',
                'work_phone': '+7 (499) 333-33-33',
            },
            {
                'last_name': 'Козлова',
                'first_name_patronymic': 'Анна Николаевна',
                'position': 'Секретарь',
                'address': 'г. Москва, Проспект Мира, д. 42',
                'personal_phone': '+7 (999) 444-44-44',
                'work_phone': '+7 (499) 444-44-44',
            },
            {
                'last_name': 'Смирнов',
                'first_name_patronymic': 'Дмитрий Александрович',
                'position': 'Менеджер по продажам',
                'address': 'г. Москва, ул. Садовая, д. 7',
                'personal_phone': '+7 (999) 555-55-55',
                'work_phone': '+7 (499) 555-55-55',
            },
        ]

        for emp_data in sample_employees:
            emp, created = Employee.objects.get_or_create(
                last_name=emp_data['last_name'],
                first_name_patronymic=emp_data['first_name_patronymic'],
                defaults=emp_data,
            )
            status = 'добавлен' if created else 'уже существует'
            self.stdout.write(f'  Сотрудник «{emp.full_name}» — {status}')

        self.stdout.write(self.style.SUCCESS('\nНастройка завершена! Логины для теста:'))
        self.stdout.write('  director  / director123  — полный доступ')
        self.stdout.write('  deputy    / deputy123    — редактирование')
        self.stdout.write('  secretary / secretary123 — только просмотр')
        self.stdout.write('  (без входа)              — гость')
