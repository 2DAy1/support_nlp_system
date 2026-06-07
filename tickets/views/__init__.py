from tickets.views.dashboard import DashboardView
from tickets.views.statistics import TicketStatisticsView
from tickets.views.tickets import (
    TicketCreateView,
    TicketDetailView,
    TicketListView,
)


__all__ = [
    'DashboardView',
    'TicketCreateView',
    'TicketDetailView',
    'TicketListView',
    'TicketStatisticsView',
]
