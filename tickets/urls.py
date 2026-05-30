from django.urls import path

from tickets.views import (
    TicketCreateView,
    TicketDetailView,
    TicketListView,
    TicketStatisticsView,
)


urlpatterns = [
    path('', TicketListView.as_view(), name='ticket_list'),
    path('create/', TicketCreateView.as_view(), name='ticket_create'),
    path('statistics/', TicketStatisticsView.as_view(), name='ticket_statistics'),
    path('tickets/<int:ticket_id>/', TicketDetailView.as_view(), name='ticket_detail'),
]