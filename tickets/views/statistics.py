from django.views.generic import TemplateView

from tickets.selectors.statistics import (
    get_tickets_by_category,
    get_tickets_by_department,
    get_tickets_by_source,
    get_tickets_by_status,
)
from tickets.views.tickets import CompanyAccessMixin


class TicketStatisticsView(CompanyAccessMixin, TemplateView):
    template_name = 'tickets/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_company_queryset()

        context['total_tickets'] = queryset.count()
        context['tickets_by_category'] = get_tickets_by_category(queryset)
        context['tickets_by_department'] = get_tickets_by_department(queryset)
        context['tickets_by_status'] = get_tickets_by_status(queryset)
        context['tickets_by_source'] = get_tickets_by_source(queryset)

        return context
