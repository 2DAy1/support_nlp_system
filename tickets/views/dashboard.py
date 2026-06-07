from django.views.generic import TemplateView

from tickets.selectors.statistics import (
    get_ticket_status_counts,
    get_tickets_by_category,
    get_tickets_by_source,
)
from tickets.views.tickets import CompanyAccessMixin


class DashboardView(CompanyAccessMixin, TemplateView):
    template_name = 'tickets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_company_queryset()

        context.update(get_ticket_status_counts(queryset))
        context['latest_tickets'] = queryset[:5]
        context['tickets_by_source'] = get_tickets_by_source(queryset)[:5]
        context['tickets_by_category'] = get_tickets_by_category(queryset)[:5]

        return context
