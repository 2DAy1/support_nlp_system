import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tickets.models import (
    Category,
    Company,
    CompanyApiKey,
    Department,
    Source,
    Ticket,
    TicketComment,
    TicketHistory,
    UserProfile,
)
from tickets.services.classifier import TicketClassifier
from tickets.services.routing import TicketRoutingService


class BaseTicketTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name='Test Company',
            description='Test company',
        )

        cls.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123',
        )

        cls.profile = UserProfile.objects.create(
            user=cls.user,
            company=cls.company,
            role=UserProfile.Role.COMPANY_ADMIN,
        )

        cls.source = Source.objects.create(
            company=cls.company,
            name='Website form',
            source_type=Source.SourceType.WEBSITE,
        )

        cls.api_key = CompanyApiKey.objects.create(
            company=cls.company,
            name='Test API key',
        )

        cls.auth_department = Department.objects.create(
            company=cls.company,
            name='Відділ авторизації',
        )

        cls.payment_department = Department.objects.create(
            company=cls.company,
            name='Фінансовий відділ',
        )

        cls.tech_department = Department.objects.create(
            company=cls.company,
            name='Технічна підтримка',
        )

        cls.consulting_department = Department.objects.create(
            company=cls.company,
            name='Консультаційний відділ',
        )

        cls.other_department = Department.objects.create(
            company=cls.company,
            name='Загальний відділ підтримки',
        )

        Category.objects.create(
            company=cls.company,
            name='Авторизація',
            department=cls.auth_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Оплата',
            department=cls.payment_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Технічна помилка',
            department=cls.tech_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Консультація',
            department=cls.consulting_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Інше',
            department=cls.other_department,
        )


class TicketModelTests(BaseTicketTestCase):
    def test_company_can_be_created(self):
        self.assertEqual(self.company.name, 'Test Company')
        self.assertTrue(self.company.is_active)

    def test_source_belongs_to_company(self):
        self.assertEqual(self.source.company, self.company)
        self.assertEqual(self.source.source_type, Source.SourceType.WEBSITE)

    def test_api_key_belongs_to_company(self):
        self.assertEqual(self.api_key.company, self.company)
        self.assertTrue(self.api_key.key)
        self.assertTrue(self.api_key.is_active)

    def test_user_profile_belongs_to_company(self):
        self.assertEqual(self.profile.company, self.company)
        self.assertTrue(self.profile.is_company_admin)


class TicketClassifierTests(TestCase):
    def test_classifier_returns_expected_category(self):
        model_path = (
            settings.BASE_DIR
            / Path('ml/artifacts/ticket_classifier.joblib')
        )

        if not model_path.exists():
            self.skipTest(
                'Trained classifier model not found. '
                'Run: py manage.py train_classifier'
            )

        classifier = TicketClassifier()
        result = classifier.classify(
            'Не можу увійти в акаунт, система не приймає пароль'
        )

        self.assertEqual(result.category_name, 'Авторизація')
        self.assertGreater(result.confidence, 0)


class TicketRoutingServiceTests(BaseTicketTestCase):
    def test_create_ticket_classifies_and_routes_ticket(self):
        service = TicketRoutingService()

        ticket = service.create_ticket(
            company=self.company,
            source=self.source,
            created_by=self.user,
            title='Не можу увійти',
            text='Система не приймає пароль',
            author_name='Test Client',
            author_email='client@example.com',
            rating=2,
        )

        self.assertEqual(ticket.company, self.company)
        self.assertEqual(ticket.source, self.source)
        self.assertEqual(ticket.category.name, 'Авторизація')
        self.assertEqual(ticket.department.name, 'Відділ авторизації')
        self.assertEqual(ticket.status, Ticket.Status.NEW)
        self.assertGreater(ticket.confidence, 0)

    def test_create_ticket_creates_initial_history_events(self):
        service = TicketRoutingService()

        ticket = service.create_ticket(
            company=self.company,
            source=self.source,
            created_by=self.user,
            title='Проблема з оплатою',
            text='Гроші списались але замовлення не створилось',
        )

        event_types = list(
            TicketHistory.objects
            .filter(ticket=ticket)
            .values_list('event_type', flat=True)
        )

        self.assertIn(TicketHistory.EventType.CREATED, event_types)
        self.assertIn(TicketHistory.EventType.CLASSIFIED, event_types)
        self.assertIn(TicketHistory.EventType.ROUTED, event_types)

    def test_update_status_changes_ticket_status(self):
        service = TicketRoutingService()

        ticket = service.create_ticket(
            company=self.company,
            source=self.source,
            created_by=self.user,
            title='Проблема з оплатою',
            text='Не можу оплатити замовлення',
        )

        service.update_status(
            ticket=ticket,
            new_status=Ticket.Status.IN_PROGRESS,
            changed_by=self.user,
        )

        ticket.refresh_from_db()

        self.assertEqual(ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertTrue(
            TicketHistory.objects.filter(
                ticket=ticket,
                event_type=TicketHistory.EventType.STATUS_CHANGED,
            ).exists()
        )


class TicketApiTests(BaseTicketTestCase):
    def test_api_creates_ticket_with_valid_api_key(self):
        payload = {
            'source': 'Website form',
            'external_id': 'test-api-001',
            'author_name': 'Іван Петренко',
            'author_email': 'ivan@example.com',
            'rating': 2,
            'title': 'Не можу увійти',
            'text': 'Система не приймає пароль',
        }

        response = self.client.post(
            reverse('api_create_ticket'),
            data=json.dumps(payload, ensure_ascii=False),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key,
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data['company'], self.company.name)
        self.assertEqual(data['source'], self.source.name)
        self.assertEqual(data['category'], 'Авторизація')
        self.assertEqual(data['department'], 'Відділ авторизації')
        self.assertEqual(data['status'], Ticket.Status.NEW)

        self.assertTrue(
            Ticket.objects.filter(
                external_id='test-api-001',
                company=self.company,
            ).exists()
        )

    def test_api_rejects_request_without_api_key(self):
        payload = {
            'title': 'Test',
            'text': 'Test',
        }

        response = self.client.post(
            reverse('api_create_ticket'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()['error'],
            'Invalid or missing API key.',
        )

    def test_api_validates_required_fields(self):
        response = self.client.post(
            reverse('api_create_ticket'),
            data=json.dumps({'title': 'Only title'}),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('text', response.json()['error'])

    def test_api_validates_rating_range(self):
        payload = {
            'title': 'Test',
            'text': 'Test',
            'rating': 10,
        }

        response = self.client.post(
            reverse('api_create_ticket'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_API_KEY=self.api_key.key,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('rating', response.json()['error'])


class TicketViewTests(BaseTicketTestCase):
    def setUp(self):
        self.client.login(
            username='manager',
            password='testpass123',
        )

        self.ticket = TicketRoutingService().create_ticket(
            company=self.company,
            source=self.source,
            created_by=self.user,
            title='Не можу увійти',
            text='Система не приймає пароль',
        )

    def test_dashboard_is_available_for_company_user(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    def test_ticket_list_shows_company_tickets(self):
        response = self.client.get(reverse('ticket_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket.title)

    def test_ticket_detail_is_available(self):
        response = self.client.get(
            reverse(
                'ticket_detail',
                kwargs={'ticket_id': self.ticket.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket.title)

    def test_ticket_status_can_be_changed(self):
        response = self.client.post(
            reverse(
                'ticket_detail',
                kwargs={'ticket_id': self.ticket.id},
            ),
            data={
                'action': 'update_status',
                'status': Ticket.Status.IN_PROGRESS,
                'assigned_user': self.user.id,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.status,
            Ticket.Status.IN_PROGRESS,
        )
        self.assertEqual(
            self.ticket.assigned_user,
            self.user,
        )
        self.assertTrue(
            TicketHistory.objects.filter(
                ticket=self.ticket,
                event_type=TicketHistory.EventType.STATUS_CHANGED,
            ).exists()
        )

    def test_ticket_comment_can_be_added(self):
        response = self.client.post(
            reverse(
                'ticket_detail',
                kwargs={'ticket_id': self.ticket.id},
            ),
            data={
                'action': 'add_comment',
                'text': 'Перевірити звернення менеджером.',
                'is_internal': 'on',
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            TicketComment.objects.filter(
                ticket=self.ticket,
                text='Перевірити звернення менеджером.',
            ).exists()
        )
        self.assertTrue(
            TicketHistory.objects.filter(
                ticket=self.ticket,
                event_type=TicketHistory.EventType.COMMENT_ADDED,
            ).exists()
        )

    def test_statistics_page_is_available(self):
        response = self.client.get(reverse('statistics'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Статистика')