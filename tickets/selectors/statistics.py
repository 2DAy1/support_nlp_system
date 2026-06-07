from django.db.models import Count

from tickets.models import Ticket


def get_ticket_status_counts(queryset):
    return {
        'total_tickets': queryset.count(),
        'new_tickets': queryset.filter(status=Ticket.Status.NEW).count(),
        'in_progress_tickets': queryset.filter(
            status=Ticket.Status.IN_PROGRESS
        ).count(),
        'resolved_tickets': queryset.filter(
            status=Ticket.Status.RESOLVED
        ).count(),
        'closed_tickets': queryset.filter(status=Ticket.Status.CLOSED).count(),
    }


def get_tickets_by_category(queryset):
    return (
        queryset
        .values('category__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )


def get_tickets_by_department(queryset):
    return (
        queryset
        .values('department__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )


def get_tickets_by_status(queryset):
    return (
        queryset
        .values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )


def get_tickets_by_source(queryset):
    return (
        queryset
        .values('source__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
