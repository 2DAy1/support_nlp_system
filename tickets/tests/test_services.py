from pathlib import Path

from django.conf import settings
from django.test import TestCase

from tickets.models import Ticket, TicketHistory
from tickets.services.classifier import TicketClassifier
from tickets.services.routing import TicketRoutingService
from tickets.tests.test_models import BaseTicketTestCase


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
