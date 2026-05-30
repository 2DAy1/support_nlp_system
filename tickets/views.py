from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from tickets.forms import TicketCreateForm, TicketStatusForm
from tickets.models import Ticket
from tickets.services.routing import TicketRoutingService


class TicketListView(ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20


class TicketCreateView(CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_create.html'
    success_url = reverse_lazy('ticket_list')

    def form_valid(self, form):
        service = TicketRoutingService()

        service.create_ticket(
            title=form.cleaned_data['title'],
            text=form.cleaned_data['text'],
            user=self.request.user if self.request.user.is_authenticated else None
        )

        return redirect(self.success_url)


class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'
    pk_url_kwarg = 'ticket_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_form'] = TicketStatusForm(instance=self.object)
        context['history'] = self.object.history.all()

        return context

    def post(self, request, *args, **kwargs):
        ticket = get_object_or_404(Ticket, id=kwargs['ticket_id'])
        form = TicketStatusForm(request.POST, instance=ticket)

        if form.is_valid():
            service = TicketRoutingService()
            service.update_status(
                ticket=ticket,
                new_status=form.cleaned_data['status']
            )

        return redirect('ticket_detail', ticket_id=ticket.id)


class TicketStatisticsView(TemplateView):
    template_name = 'tickets/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_tickets'] = Ticket.objects.count()
        context['tickets_by_category'] = self._get_tickets_by_category()
        context['tickets_by_department'] = self._get_tickets_by_department()
        context['tickets_by_status'] = self._get_tickets_by_status()

        return context

    def _get_tickets_by_category(self):
        return (
            Ticket.objects
            .values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    def _get_tickets_by_department(self):
        return (
            Ticket.objects
            .values('department__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    def _get_tickets_by_status(self):
        return (
            Ticket.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )