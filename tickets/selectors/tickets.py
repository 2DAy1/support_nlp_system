from tickets.models import Category, Department, Source, Ticket


def get_user_company(user):
    if user.is_superuser:
        return None

    profile = getattr(user, 'profile', None)

    if not profile or not profile.is_active:
        return None

    return profile.company


def get_ticket_base_queryset():
    return Ticket.objects.select_related(
        'company',
        'source',
        'category',
        'department',
        'assigned_user',
        'created_by',
    )


def get_company_ticket_queryset(user):
    queryset = get_ticket_base_queryset()

    if user.is_superuser:
        return queryset

    company = get_user_company(user)

    if company:
        return queryset.filter(company=company)

    return queryset.none()


def get_ticket_list_queryset(user, filters):
    queryset = get_company_ticket_queryset(user)

    status = filters.get('status')
    category = filters.get('category')
    department = filters.get('department')
    source = filters.get('source')
    search = filters.get('q')

    if status:
        queryset = queryset.filter(status=status)

    if category:
        queryset = queryset.filter(category_id=category)

    if department:
        queryset = queryset.filter(department_id=department)

    if source:
        queryset = queryset.filter(source_id=source)

    if search:
        queryset = queryset.filter(title__icontains=search)

    return queryset.order_by('-created_at')


def get_ticket_filter_options():
    return {
        'statuses': Ticket.Status.choices,
        'categories': Category.objects.all(),
        'departments': Department.objects.all(),
        'sources': Source.objects.all(),
    }


def get_ticket_history(ticket):
    return ticket.history.select_related('changed_by')


def get_ticket_comments(ticket):
    return ticket.comments.select_related('author')
