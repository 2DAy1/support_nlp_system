from django.core.management.base import BaseCommand

from tickets.models import Category, Department, Ticket
from tickets.services.routing import TicketRoutingService


class Command(BaseCommand):
    help = 'Creates demo departments, categories and tickets'

    def handle(self, *args, **options):
        self._create_departments_and_categories()
        self._create_demo_tickets()

        self.stdout.write(
            self.style.SUCCESS('Demo data created successfully.')
        )

    def _create_departments_and_categories(self):
        data = {
            'Відділ авторизації': ['Авторизація'],
            'Фінансовий відділ': ['Оплата'],
            'Технічна підтримка': ['Технічна помилка'],
            'Консультаційний відділ': ['Консультація'],
            'Загальний відділ підтримки': ['Інше'],
        }

        for department_name, category_names in data.items():
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

    def _create_demo_tickets(self):
        if Ticket.objects.exists():
            return

        service = TicketRoutingService()

        demo_tickets = [
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

        for ticket in demo_tickets:
            service.create_ticket(
                title=ticket['title'],
                text=ticket['text']
            )