from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from tickets.forms import (
    TicketCommentForm,
    TicketCreateForm,
    TicketStatusForm,
)
from tickets.models import Ticket,TicketHistory
from tickets.services.routing import TicketRoutingService


class CompanyAccessMixin(LoginRequiredMixin):
    def get_user_company(self):
        if self.request.user.is_superuser:
            return None

        profile = getattr(self.request.user, 'profile', None)

        if not profile or not profile.is_active:
            return None

        return profile.company

    def get_company_queryset(self):
        queryset = Ticket.objects.select_related(
            'company',
            'source',
            'category',
            'department',
            'assigned_user',
            'created_by',
        )

        if self.request.user.is_superuser:
            return queryset

        company = self.get_user_company()

        if company:
            return queryset.filter(company=company)

        return queryset.none()


class TicketListView(CompanyAccessMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            self.get_company_queryset()
            .select_related(
                'category',
                'department',
                'source',
            )
        )

        status = self.request.GET.get('status')
        category = self.request.GET.get('category')
        department = self.request.GET.get('department')
        source = self.request.GET.get('source')
        search = self.request.GET.get('q')

        if status:
            queryset = queryset.filter(status=status)

        if category:
            queryset = queryset.filter(
                category_id=category
            )

        if department:
            queryset = queryset.filter(
                department_id=department
            )

        if source:
            queryset = queryset.filter(
                source_id=source
            )

        if search:
            queryset = queryset.filter(
                title__icontains=search
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from tickets.models import (
            Category,
            Department,
            Source,
        )

        context['statuses'] = Ticket.Status.choices
        context['categories'] = Category.objects.all()
        context['departments'] = Department.objects.all()
        context['sources'] = Source.objects.all()

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
        context['history'] = self.object.history.select_related(
            'changed_by'
        )
        context['comments'] = self.object.comments.select_related(
            'author'
        )

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
                    f'{old_assigned_user or "—"} to {assigned_user or "—"}.'
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


class TicketStatisticsView(CompanyAccessMixin, TemplateView):
    template_name = 'tickets/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_company_queryset()

        context['total_tickets'] = queryset.count()
        context['tickets_by_category'] = self._get_tickets_by_category(
            queryset
        )
        context['tickets_by_department'] = self._get_tickets_by_department(
            queryset
        )
        context['tickets_by_status'] = self._get_tickets_by_status(
            queryset
        )
        context['tickets_by_source'] = self._get_tickets_by_source(
            queryset
        )

        return context

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

    def _get_tickets_by_source(self, queryset):
        return (
            queryset
            .values('source__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

class DashboardView(CompanyAccessMixin, TemplateView):
    template_name = 'tickets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_company_queryset()

        context['total_tickets'] = queryset.count()
        context['new_tickets'] = queryset.filter(
            status=Ticket.Status.NEW
        ).count()
        context['in_progress_tickets'] = queryset.filter(
            status=Ticket.Status.IN_PROGRESS
        ).count()
        context['resolved_tickets'] = queryset.filter(
            status=Ticket.Status.RESOLVED
        ).count()
        context['closed_tickets'] = queryset.filter(
            status=Ticket.Status.CLOSED
        ).count()

        context['latest_tickets'] = queryset[:5]

        context['tickets_by_source'] = (
            queryset
            .values('source__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        context['tickets_by_category'] = (
            queryset
            .values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return context