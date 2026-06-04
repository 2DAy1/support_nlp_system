from django.urls import path

from tickets.views import (
    DashboardView,
    TicketCreateView,
    TicketDetailView,
    TicketListView,
    TicketStatisticsView,
)


urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('tickets/', TicketListView.as_view(), name='ticket_list'),
    path('create/', TicketCreateView.as_view(), name='ticket_create'),
    path(
        'tickets/<int:ticket_id>/',
        TicketDetailView.as_view(),
        name='ticket_detail'
    ),
    path('statistics/', TicketStatisticsView.as_view(), name='statistics'),
]