import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from tickets.models import Category, Department, Ticket
from tickets.services.routing import TicketRoutingService


class Command(BaseCommand):
    help = 'Creates demo departments, categories and tickets'

    DEPARTMENTS_DATA = {
        'Відділ авторизації': ['Авторизація'],
        'Фінансовий відділ': ['Оплата'],
        'Технічна підтримка': ['Технічна помилка'],
        'Консультаційний відділ': ['Консультація'],
        'Загальний відділ підтримки': ['Інше'],
    }

    DEFAULT_TICKETS = [
        {
            'title': 'Проблема з входом',
            'text': 'Не можу увійти в акаунт, забув пароль',
        },
        {
            'title': 'Помилка оплати',
            'text': 'Гроші списались з картки але послуга не активувалась',
        },
        {
            'title': 'Помилка на сайті',
            'text': 'На сайті виникає помилка 500 після відкриття сторінки',
        },
        {
            'title': 'Питання щодо профілю',
            'text': 'Підкажіть як змінити налаштування профілю',
        },
        {
            'title': 'Пропозиція',
            'text': 'Хочу залишити відгук та пропозицію щодо покращення сервісу',
        },
    ]

    RANDOM_TICKETS = [
        ('Проблема з входом', 'Не можу увійти в акаунт, забув пароль'),
        ('Не працює авторизація', 'Система не приймає логін і пароль'),
        ('Відновлення доступу', 'Потрібно відновити доступ до акаунта'),
        ('Не приходить код', 'Не приходить код підтвердження для входу'),

        ('Помилка оплати', 'Гроші списались з картки але послуга не активувалась'),
        ('Не проходить платіж', 'Не можу оплатити замовлення карткою'),
        ('Проблема з рахунком', 'Платіж не був зарахований'),
        ('Картка відхиляється', 'Картка відхиляється без пояснення причини'),

        ('Помилка на сайті', 'На сайті виникає помилка 500 після відкриття сторінки'),
        ('Не працює кнопка', 'Не працює кнопка збереження'),
        ('Сервер не відповідає', 'Сторінка зависає після входу'),
        ('Сайт не відкривається', 'Сайт не відкривається у браузері'),

        ('Питання щодо профілю', 'Підкажіть як змінити налаштування профілю'),
        ('Консультація', 'Поясніть як користуватись сервісом'),
        ('Історія замовлень', 'Де знайти історію замовлень'),
        ('Зміна email', 'Як змінити електронну пошту в профілі'),

        ('Пропозиція', 'Хочу залишити відгук та пропозицію щодо покращення сервісу'),
        ('Загальне питання', 'Маю загальне питання до адміністрації'),
        ('Інше звернення', 'Питання не стосується роботи системи'),
        ('Повідомлення', 'Хочу повідомити загальну інформацію'),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=False,
            help='Existing username for generated tickets'
        )

        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of random tickets to create for username'
        )

    def handle(self, *args, **options):
        self._create_departments_and_categories()

        username = options.get('username')

        if username:
            user = self._get_user(username)

            created_count = self._create_random_tickets(
                user=user,
                count=options['count']
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} random tickets for user "{username}".'
                )
            )

            return

        created_count = self._create_default_tickets()

        self.stdout.write(
            self.style.SUCCESS(
                f'Demo data created successfully. Created {created_count} default tickets.'
            )
        )

    def _create_departments_and_categories(self):
        for department_name, category_names in self.DEPARTMENTS_DATA.items():
            department, _ = Department.objects.get_or_create(
                name=department_name
            )

            for category_name in category_names:
                Category.objects.get_or_create(
                    name=category_name,
                    defaults={
                        'department': department,
                    }
                )

    def _get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(
                f'User "{username}" does not exist. Create this user first.'
            ) from exc

    def _create_default_tickets(self):
        if Ticket.objects.exists():
            return 0

        service = TicketRoutingService()
        created_count = 0

        for ticket in self.DEFAULT_TICKETS:
            service.create_ticket(
                title=ticket['title'],
                text=ticket['text']
            )

            created_count += 1

        return created_count

    def _create_random_tickets(self, user, count):
        service = TicketRoutingService()
        created_count = 0

        for _ in range(count):
            title, text = random.choice(self.RANDOM_TICKETS)

            service.create_ticket(
                title=title,
                text=text,
                user=user
            )

            created_count += 1

        return created_count