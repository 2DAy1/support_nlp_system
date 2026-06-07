from django.urls import reverse

from tickets.models import Ticket, TicketComment, TicketHistory
from tickets.services.routing import TicketRoutingService
from tickets.tests.test_models import BaseTicketTestCase


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
