import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from tickets.models import (
    Category,
    Company,
    CompanyApiKey,
    Department,
    Source,
    Ticket,
    UserProfile,
)
from tickets.services.routing import TicketRoutingService


class Command(BaseCommand):
    help = 'Create demo B2B data for support routing system'

    COMPANY_NAME = 'Demo Company'

    DEPARTMENTS_DATA = {
        'Відділ авторизації': ['Авторизація'],
        'Фінансовий відділ': ['Оплата'],
        'Технічна підтримка': ['Технічна помилка'],
        'Консультаційний відділ': ['Консультація'],
        'Загальний відділ підтримки': ['Інше'],
    }

    SOURCES_DATA = [
        ('Manual input', Source.SourceType.MANUAL),
        ('Website form', Source.SourceType.WEBSITE),
        ('Google Maps reviews', Source.SourceType.GOOGLE_MAPS),
        ('CRM import', Source.SourceType.CRM),
        ('API integration', Source.SourceType.API),
        ('Email support', Source.SourceType.EMAIL),
    ]

    RANDOM_TICKETS = [
        (
            'Проблема з входом',
            'Не можу увійти в акаунт, забув пароль',
            2,
        ),
        (
            'Не працює авторизація',
            'Система не приймає логін і пароль',
            2,
        ),
        (
            'Відновлення доступу',
            'Потрібно відновити доступ до акаунта',
            3,
        ),
        (
            'Не приходить код',
            'Не приходить код підтвердження для входу',
            2,
        ),
        (
            'Помилка оплати',
            'Гроші списались з картки але послуга не активувалась',
            1,
        ),
        (
            'Не проходить платіж',
            'Не можу оплатити замовлення карткою',
            2,
        ),
        (
            'Проблема з рахунком',
            'Платіж не був зарахований',
            1,
        ),
        (
            'Картка відхиляється',
            'Картка відхиляється без пояснення причини',
            2,
        ),
        (
            'Помилка на сайті',
            'На сайті виникає помилка 500 після відкриття сторінки',
            1,
        ),
        (
            'Не працює кнопка',
            'Не працює кнопка збереження',
            3,
        ),
        (
            'Сервер не відповідає',
            'Сторінка зависає після входу',
            2,
        ),
        (
            'Сайт не відкривається',
            'Сайт не відкривається у браузері',
            1,
        ),
        (
            'Питання щодо профілю',
            'Підкажіть як змінити налаштування профілю',
            4,
        ),
        (
            'Консультація',
            'Поясніть як користуватись сервісом',
            4,
        ),
        (
            'Історія замовлень',
            'Де знайти історію замовлень',
            4,
        ),
        (
            'Зміна email',
            'Як змінити електронну пошту в профілі',
            4,
        ),
        (
            'Пропозиція',
            'Хочу залишити відгук та пропозицію щодо покращення сервісу',
            5,
        ),
        (
            'Загальне питання',
            'Маю загальне питання до адміністрації',
            5,
        ),
        (
            'Інше звернення',
            'Питання не стосується роботи системи',
            3,
        ),
        (
            'Повідомлення',
            'Хочу повідомити загальну інформацію',
            4,
        ),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=False,
            help='Existing manager username'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=30,
            help='Number of demo tickets'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete old demo tickets before creating new ones'
        )

    def handle(self, *args, **options):
        company = self._get_or_create_company()
        self._create_departments_and_categories(company)
        sources = self._create_sources(company)
        self._create_api_key(company)

        user = None
        username = options.get('username')

        if username:
            user = self._get_user(username)
            self._create_user_profile(user=user, company=company)

        if options['clear']:
            self._clear_company_tickets(company)

        created_count = self._create_random_tickets(
            company=company,
            sources=sources,
            user=user,
            count=options['count'],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Demo data created successfully. '
                f'Company: "{company.name}". '
                f'Created tickets: {created_count}.'
            )
        )

    def _get_or_create_company(self):
        company, _ = Company.objects.get_or_create(
            name=self.COMPANY_NAME,
            defaults={
                'description': (
                    'Demo company for B2B support routing system.'
                ),
                'is_active': True,
            }
        )

        return company

    def _create_departments_and_categories(self, company):
        for department_name, category_names in self.DEPARTMENTS_DATA.items():
            department, _ = Department.objects.get_or_create(
                company=company,
                name=department_name,
                defaults={
                    'is_active': True,
                }
            )

            for category_name in category_names:
                Category.objects.get_or_create(
                    company=company,
                    name=category_name,
                    defaults={
                        'department': department,
                        'is_active': True,
                    }
                )

    def _create_sources(self, company):
        sources = []

        for source_name, source_type in self.SOURCES_DATA:
            source, _ = Source.objects.get_or_create(
                company=company,
                name=source_name,
                defaults={
                    'source_type': source_type,
                    'is_active': True,
                }
            )
            sources.append(source)

        return sources

    def _create_api_key(self, company):
        api_key, _ = CompanyApiKey.objects.get_or_create(
            company=company,
            name='Demo API key',
            defaults={
                'is_active': True,
            }
        )

        return api_key

    def _get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(
                f'User "{username}" does not exist. '
                f'Create this user first.'
            ) from exc

    def _create_user_profile(self, user, company):
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'company': company,
                'role': UserProfile.Role.COMPANY_ADMIN,
                'is_active': True,
            }
        )

    def _clear_company_tickets(self, company):
        Ticket.objects.filter(company=company).delete()

    def _create_random_tickets(self, company, sources, user, count):
        service = TicketRoutingService()
        created_count = 0

        for index in range(count):
            title, text, rating = random.choice(self.RANDOM_TICKETS)
            source = random.choice(sources)

            service.create_ticket(
                title=title,
                text=text,
                company=company,
                source=source,
                created_by=user,
                external_id=f'demo-{index + 1}',
                author_name=f'Client {index + 1}',
                author_email=f'client{index + 1}@example.com',
                rating=rating,
                raw_payload={
                    'source': source.name,
                    'source_type': source.source_type,
                    'demo': True,
                },
            )

            created_count += 1

        return created_count