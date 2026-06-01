from django.db import transaction

from tickets.models import Category, Ticket, TicketHistory
from tickets.services.classifier import TicketClassifier


class TicketRoutingService:
    MIN_CONFIDENCE = 25

    def __init__(self):
        self.classifier = TicketClassifier()

    @transaction.atomic
    def create_ticket(self, title: str, text: str, user=None) -> Ticket:
        result = self.classifier.classify(text)

        category_name = self._get_final_category_name(
            result.category_name,
            result.confidence
        )

        category = self._get_category(category_name)

        return Ticket.objects.create(
            user=user,
            title=title,
            text=text,
            category=category,
            department=category.department if category else None,
            confidence=result.confidence
        )

    @transaction.atomic
    def update_status(self, ticket: Ticket, new_status: str) -> Ticket:
        old_status = ticket.status

        if old_status == new_status:
            return ticket

        ticket.status = new_status
        ticket.save(update_fields=['status', 'updated_at'])

        TicketHistory.objects.create(
            ticket=ticket,
            old_status=old_status,
            new_status=new_status
        )

        return ticket

    def _get_final_category_name(self, category_name: str, confidence: float) -> str:
        if confidence < self.MIN_CONFIDENCE:
            return 'Інше'

        return category_name

    def _get_category(self, category_name: str) -> Category | None:
        return Category.objects.filter(name=category_name).select_related('department').first()