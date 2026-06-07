import json

from django.urls import reverse

from tickets.models import Ticket
from tickets.tests.test_models import BaseTicketTestCase


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
