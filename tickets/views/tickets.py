from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from tickets.forms import (
    TicketCommentForm,
    TicketCreateForm,
    TicketStatusForm,
)
from tickets.models import Ticket, TicketHistory
from tickets.selectors.tickets import (
    get_company_ticket_queryset,
    get_ticket_comments,
    get_ticket_filter_options,
    get_ticket_history,
    get_ticket_list_queryset,
    get_user_company,
)
from tickets.services.routing import TicketRoutingService


class CompanyAccessMixin(LoginRequiredMixin):
    def get_user_company(self):
        return get_user_company(self.request.user)

    def get_company_queryset(self):
        return get_company_ticket_queryset(self.request.user)


class TicketListView(CompanyAccessMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        return get_ticket_list_queryset(
            user=self.request.user,
            filters=self.request.GET,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_ticket_filter_options())

        return context


class TicketCreateView(CompanyAccessMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_create.html'
    success_url = reverse_lazy('ticket_list')

    def form_valid(self, form):
        company = self.get_user_company()

        if not company and not self.request.user.is_superuser:
            return redirect('ticket_list')

        service = TicketRoutingService()

        service.create_ticket(
            title=form.cleaned_data['title'],
            text=form.cleaned_data['text'],
            company=company,
            created_by=self.request.user,
        )

        return redirect(self.success_url)


class TicketDetailView(CompanyAccessMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'
    pk_url_kwarg = 'ticket_id'

    def get_queryset(self):
        return self.get_company_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_form'] = TicketStatusForm(instance=self.object)
        context['comment_form'] = TicketCommentForm()
        context['history'] = get_ticket_history(self.object)
        context['comments'] = get_ticket_comments(self.object)

        return context

    def post(self, request, *args, **kwargs):
        ticket = get_object_or_404(
            self.get_queryset(),
            id=kwargs['ticket_id'],
        )

        action = request.POST.get('action')

        if action == 'update_status':
            self._update_ticket_status(
                request=request,
                ticket=ticket,
            )

        if action == 'add_comment':
            self._add_ticket_comment(
                request=request,
                ticket=ticket,
            )

        return redirect('ticket_detail', ticket_id=ticket.id)

    def _update_ticket_status(self, request, ticket):
        old_status = ticket.status
        old_assigned_user = ticket.assigned_user

        form = TicketStatusForm(
            request.POST,
            instance=ticket,
        )

        if not form.is_valid():
            return

        new_status = form.cleaned_data['status']
        assigned_user = form.cleaned_data['assigned_user']

        ticket.status = old_status

        service = TicketRoutingService()
        service.update_status(
            ticket=ticket,
            new_status=new_status,
            changed_by=request.user,
        )

        ticket.assigned_user = assigned_user
        ticket.save(
            update_fields=[
                'assigned_user',
                'updated_at',
            ]
        )

        if old_assigned_user != assigned_user:
            TicketHistory.objects.create(
                ticket=ticket,
                changed_by=request.user,
                event_type=TicketHistory.EventType.ASSIGNED,
                comment=(
                    f'Assigned user changed from '
                    f'{old_assigned_user or "â€”"} to {assigned_user or "â€”"}.'
                ),
            )

    def _add_ticket_comment(self, request, ticket):
        form = TicketCommentForm(request.POST)

        if not form.is_valid():
            return

        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        comment.save()

        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            event_type=TicketHistory.EventType.COMMENT_ADDED,
            comment='Comment added.',
        )
