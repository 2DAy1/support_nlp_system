from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import User

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

        self.department = Department.objects.get(name='Відділ авторизації')
        self.category = Category.objects.get(name='Авторизація')

    def test_create_ticket_with_user(self):
        user = User.objects.create_user(
            username='client',
            password='testpass123'
        )

        service = TicketRoutingService()

        ticket = service.create_ticket(
            title='Проблема з входом',
            text='Не можу увійти в акаунт, забув пароль від особистого кабінету',
            user=user
        )

        self.assertEqual(ticket.user, user)

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
        self.user = User.objects.create_user(
            username='client',
            password='testpass123'
        )

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

    def test_ticket_create_page_requires_login(self):
        response = self.client.get(reverse('ticket_create'))

        self.assertEqual(response.status_code, 302)

    def test_ticket_can_be_created(self):
        self.client.login(
            username='client',
            password='testpass123'
        )

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
        self.client.login(
            username='client',
            password='testpass123'
        )

        response = self.client.get(
            reverse('ticket_statistics')
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_authenticated_user_can_create_ticket(self):
        user = self.user

        self.client.login(
            username='client',
            password='testpass123'
        )

        response = self.client.post(
            reverse('ticket_create'),
            {
                'title': 'Проблема з входом',
                'text': 'Не можу увійти в акаунт, забув пароль від особистого кабінету',
            }
        )

        ticket = Ticket.objects.first()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ticket.user, user)

    def test_authenticated_user_can_open_ticket_create_page(self):
        self.client.login(
            username='client',
            password='testpass123'
        )

        response = self.client.get(reverse('ticket_create'))

        self.assertEqual(response.status_code, 200)

    def test_regular_user_cannot_change_ticket_status(self):
        ticket = TicketRoutingService().create_ticket(
            title='Проблема з входом',
            text='Не можу увійти в акаунт, забув пароль від особистого кабінету',
            user=self.user
        )

        self.client.login(
            username='client',
            password='testpass123'
        )

        response = self.client.post(
            reverse('ticket_detail', kwargs={'ticket_id': ticket.id}),
            {
                'status': Ticket.Status.IN_PROGRESS.value,
            }
        )

        ticket.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ticket.status, Ticket.Status.NEW)
        self.assertEqual(TicketHistory.objects.count(), 0)

    def test_staff_user_can_change_ticket_status(self):
        staff_user = User.objects.create_user(
            username='operator',
            password='testpass123',
            is_staff=True
        )

        ticket = TicketRoutingService().create_ticket(
            title='Проблема з входом',
            text='Не можу увійти в акаунт, забув пароль від особистого кабінету',
            user=self.user
        )

        self.client.force_login(staff_user)

        response = self.client.post(
            reverse('ticket_detail', kwargs={'ticket_id': ticket.id}),
            {
                'status': Ticket.Status.IN_PROGRESS.value,
            }
        )

        ticket.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ticket.status, Ticket.Status.IN_PROGRESS.value)
        self.assertEqual(TicketHistory.objects.count(), 1)

def test_classify_api_returns_category(self):
    response = self.client.post(
        reverse('api_classify_ticket'),
        data='{"text": "Не можу увійти в акаунт, забув пароль"}',
        content_type='application/json'
    )

    self.assertEqual(response.status_code, 200)
    self.assertIn('category', response.json())
    self.assertIn('department', response.json())
    self.assertIn('confidence', response.json())