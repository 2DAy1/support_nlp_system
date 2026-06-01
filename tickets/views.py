from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from tickets.forms import TicketCreateForm, TicketStatusForm
from tickets.models import Ticket
from tickets.services.routing import TicketRoutingService


class TicketListView(ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Ticket.objects.select_related(
            'user',
            'category',
            'department'
        )

        if self.request.user.is_authenticated and self.request.user.is_staff:
            return queryset

        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)

        return Ticket.objects.none()


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_create.html'
    success_url = reverse_lazy('ticket_list')

    def form_valid(self, form):
        service = TicketRoutingService()

        user = self.request.user if self.request.user.is_authenticated else None

        service.create_ticket(
            title=form.cleaned_data['title'],
            text=form.cleaned_data['text'],
            user=user
        )

        return redirect(self.success_url)

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'
    pk_url_kwarg = 'ticket_id'

    def get_queryset(self):
        queryset = Ticket.objects.select_related(
            'user',
            'category',
            'department'
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_form'] = TicketStatusForm(instance=self.object)
        context['history'] = self.object.history.all()

        return context

    def post(self, request, *args, **kwargs):
        ticket = get_object_or_404(
            self.get_queryset(),
            id=kwargs['ticket_id']
        )

        if not request.user.is_staff:
            return redirect('ticket_detail', ticket_id=ticket.id)

        new_status = request.POST.get('status')

        if new_status in Ticket.Status.values:
            service = TicketRoutingService()
            service.update_status(
                ticket=ticket,
                new_status=new_status
            )

        return redirect('ticket_detail', ticket_id=ticket.id)


class TicketStatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self._get_base_queryset()

        context['total_tickets'] = queryset.count()
        context['tickets_by_category'] = self._get_tickets_by_category(queryset)
        context['tickets_by_department'] = self._get_tickets_by_department(queryset)
        context['tickets_by_status'] = self._get_tickets_by_status(queryset)

        return context

    def _get_base_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.all()

        return Ticket.objects.filter(user=self.request.user)

    def _get_tickets_by_category(self, queryset):
        return (
            queryset
            .values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    def _get_tickets_by_department(self, queryset):
        return (
            queryset
            .values('department__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    def _get_tickets_by_status(self, queryset):
        return (
            queryset
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )