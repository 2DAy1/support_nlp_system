from django.urls import path

from tickets.api.views import ClassifyTicketApiView, TicketCreateApiView


urlpatterns = [
    path(
        'classify/',
        ClassifyTicketApiView.as_view(),
        name='api_classify_ticket',
    ),
    path(
        'tickets/',
        TicketCreateApiView.as_view(),
        name='api_create_ticket',
    ),
]
