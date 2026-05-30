from django.test import TestCase
from django.urls import reverse

from tickets.models import (
    Category,
    Department,
    Ticket,
    TicketHistory,
)
from tickets.services.classifier import TicketClassifier
from tickets.services.routing import TicketRoutingService


class TicketClassifierTests(TestCase):

    def test_classifier_returns_authorization_category(self):
        classifier = TicketClassifier()

        result = classifier.classify(
            'Не можу увійти в акаунт, забув пароль'
        )

        self.assertEqual(
            result.category_name,
            'Авторизація'
        )

        self.assertGreater(
            result.confidence,
            0
        )

    def test_classifier_returns_payment_category(self):
        classifier = TicketClassifier()

        result = classifier.classify(
            'Гроші списались з картки але послуга не активувалась'
        )

        self.assertEqual(
            result.category_name,
            'Оплата'
        )

        self.assertGreater(
            result.confidence,
            0
        )

    def test_classifier_returns_technical_category(self):
        classifier = TicketClassifier()

        result = classifier.classify(
            'На сайті виникає помилка 500'
        )

        self.assertEqual(
            result.category_name,
            'Технічна помилка'
        )


class TicketRoutingServiceTests(TestCase):

    def setUp(self):
        departments_data = {
            'Відділ авторизації': ['Авторизація'],
            'Фінансовий відділ': ['Оплата'],
            'Технічна підтримка': ['Технічна помилка'],
            'Консультаційний відділ': ['Консультація'],
            'Загальний відділ підтримки': ['Інше'],
        }

        for department_name, category_names in departments_data.items():
            department = Department.objects.create(name=department_name)

            for category_name in category_names:
                Category.objects.create(
                    name=category_name,
                    department=department
                )

    def test_create_ticket(self):
        service = TicketRoutingService()

        ticket = service.create_ticket(
            title='Проблема з входом',
            text='Не можу увійти в акаунт'
        )

        self.assertEqual(
            ticket.category.name,
            'Авторизація'
        )

        self.assertEqual(
            ticket.department.name,
            'Відділ авторизації'
        )

        self.assertEqual(
            ticket.status,
            Ticket.Status.NEW
        )

    def test_update_status(self):
        ticket = Ticket.objects.create(
            title='Проблема з входом',
            text='Не можу увійти',
            category=self.category,
            department=self.department
        )

        service = TicketRoutingService()

        service.update_status(
            ticket=ticket,
            new_status=Ticket.Status.IN_PROGRESS
        )

        ticket.refresh_from_db()

        self.assertEqual(
            ticket.status,
            Ticket.Status.IN_PROGRESS
        )

    def test_update_status_creates_history(self):
        ticket = Ticket.objects.create(
            title='Проблема з входом',
            text='Не можу увійти',
            category=self.category,
            department=self.department
        )

        service = TicketRoutingService()

        service.update_status(
            ticket=ticket,
            new_status=Ticket.Status.IN_PROGRESS
        )

        self.assertEqual(
            TicketHistory.objects.count(),
            1
        )

        history = TicketHistory.objects.first()

        self.assertEqual(
            history.old_status,
            Ticket.Status.NEW
        )

        self.assertEqual(
            history.new_status,
            Ticket.Status.IN_PROGRESS
        )


class TicketViewsTests(TestCase):

    def setUp(self):
        departments_data = {
            'Відділ авторизації': ['Авторизація'],
            'Фінансовий відділ': ['Оплата'],
            'Технічна підтримка': ['Технічна помилка'],
            'Консультаційний відділ': ['Консультація'],
            'Загальний відділ підтримки': ['Інше'],
        }

        for department_name, category_names in departments_data.items():
            department = Department.objects.create(name=department_name)

            for category_name in category_names:
                Category.objects.create(
                    name=category_name,
                    department=department
                )

    def test_ticket_list_page(self):
        response = self.client.get(
            reverse('ticket_list')
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_ticket_create_page(self):
        response = self.client.get(
            reverse('ticket_create')
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_ticket_can_be_created(self):
        response = self.client.post(
            reverse('ticket_create'),
            {
                'title': 'Проблема з входом',
                'text': 'Не можу увійти в акаунт'
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            Ticket.objects.count(),
            1
        )

    def test_statistics_page(self):
        response = self.client.get(
            reverse('ticket_statistics')
        )

        self.assertEqual(
            response.status_code,
            200
        )