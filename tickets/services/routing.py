from django.db import transaction

from tickets.models import (
    Category,
    Company,
    Source,
    Ticket,
    TicketHistory,
)
from tickets.services.classifier import TicketClassifier
from tickets.services.email_service import (
    EmailService
)


class TicketRoutingService:
    MIN_CONFIDENCE = 25

    def __init__(self):
        self.classifier = TicketClassifier()

    @transaction.atomic
    def create_ticket(
        self,
        title: str,
        text: str,
        company: Company,
        source: Source | None = None,
        created_by=None,
        assigned_user=None,
        external_id: str = '',
        author_name: str = '',
        author_email: str = '',
        rating: int | None = None,
        raw_payload: dict | None = None,
    ) -> Ticket:
        full_text = f'{title} {text}'.strip()
        result = self.classifier.classify(full_text)

        category_name = self._get_final_category_name(
            category_name=result.category_name,
            confidence=result.confidence
        )
        category = self._get_category(
            category_name=category_name,
            company=company
        )

        ticket = Ticket.objects.create(
            company=company,
            source=source,
            created_by=created_by,
            assigned_user=assigned_user,
            title=title,
            text=text,
            external_id=external_id,
            author_name=author_name,
            author_email=author_email,
            rating=rating,
            raw_payload=raw_payload or {},
            category=category,
            department=category.department if category else None,
            confidence=result.confidence,
        )

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=created_by,
            event_type=TicketHistory.EventType.CREATED,
            new_status=ticket.status,
            comment='Ticket created.'
        )

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=created_by,
            event_type=TicketHistory.EventType.CLASSIFIED,
            comment=f'Category: {ticket.category}. Confidence: {ticket.confidence:.2f}%.'
        )

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=created_by,
            event_type=TicketHistory.EventType.ROUTED,
            comment=f'Department: {ticket.department}.'
        )

        return ticket

    @transaction.atomic
    def update_status(
            self,
            ticket: Ticket,
            new_status: str,
            changed_by=None,
            comment: str = '',
    ) -> Ticket:
        old_status = ticket.status

        if old_status == new_status:
            return ticket

        ticket.status = new_status
        ticket.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=changed_by,
            event_type=TicketHistory.EventType.STATUS_CHANGED,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
        )

        return ticket

    def _get_final_category_name(
        self,
        category_name: str,
        confidence: float
    ) -> str:
        if confidence < self.MIN_CONFIDENCE:
            return 'Інше'

        return category_name

    def _get_category(
        self,
        category_name: str,
        company: Company
    ) -> Category | None:
        return (
            Category.objects
            .select_related('department')
            .filter(
                company=company,
                name=category_name,
                is_active=True,
            )
            .first()
        )