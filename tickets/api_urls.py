from django.urls import path

from tickets.api_views import ClassifyTicketApiView


urlpatterns = [
    path('classify/', ClassifyTicketApiView.as_view(), name='api_classify_ticket'),
]