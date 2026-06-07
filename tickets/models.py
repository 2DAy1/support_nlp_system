from secrets import token_urlsafe

from django.conf import settings
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class Role(models.TextChoices):
        COMPANY_ADMIN = 'company_admin', 'Company Admin'
        MANAGER = 'manager', 'Manager'
        OPERATOR = 'operator', 'Operator'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users'
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.MANAGER
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company__name', 'user__username']
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'

    def __str__(self):
        return f'{self.user.username} — {self.company.name}'

    @property
    def is_company_admin(self):
        return self.role == self.Role.COMPANY_ADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR


class Source(models.Model):
    class SourceType(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        API = 'api', 'API'
        WEBSITE = 'website', 'Website'
        GOOGLE_MAPS = 'google_maps', 'Google Maps'
        EMAIL = 'email', 'Email'
        CRM = 'crm', 'CRM'

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='sources'
    )
    name = models.CharField(max_length=150)
    source_type = models.CharField(
        max_length=30,
        choices=SourceType.choices,
        default=SourceType.MANUAL
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_source_name_per_company'
            )
        ]
        verbose_name = 'Source'
        verbose_name_plural = 'Sources'

    def __str__(self):
        return f'{self.company.name}: {self.name}'


class CompanyApiKey(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    name = models.CharField(max_length=150)
    key = models.CharField(max_length=255, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['company__name', 'name']
        verbose_name = 'Company API key'
        verbose_name_plural = 'Company API keys'

    def __str__(self):
        return f'{self.company.name}: {self.name}'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = token_urlsafe(32)

        super().save(*args, **kwargs)


class Department(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['company__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_department_name_per_company'
            )
        ]
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f'{self.company.name}: {self.name}'


class Category(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['company__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_category_name_per_company'
            )
        ]
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f'{self.company.name}: {self.name}'


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    source = models.ForeignKey(
        Source,
        on_delete=models.SET_NULL,
        related_name='tickets',
        null=True,
        blank=True
    )
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_tickets',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    text = models.TextField()
    external_id = models.CharField(max_length=255, blank=True)
    author_name = models.CharField(max_length=255, blank=True)
    author_email = models.EmailField(blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )
    confidence = models.FloatField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    manager_note = models.TextField(
        blank=True,
        default=''
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['external_id']),
        ]
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    def __str__(self):
        return self.title


class TicketHistory(models.Model):
    class EventType(models.TextChoices):
        CREATED = 'created', 'Created'
        CLASSIFIED = 'classified', 'Classified'
        ROUTED = 'routed', 'Routed'
        ASSIGNED = 'assigned', 'Assigned'
        STATUS_CHANGED = 'status_changed', 'Status Changed'
        COMMENT_ADDED = 'comment_added', 'Comment Added'
        CLOSED = 'closed', 'Closed'

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='history'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='ticket_status_changes',
        null=True,
        blank=True
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.STATUS_CHANGED
    )
    old_status = models.CharField(
        max_length=20,
        choices=Ticket.Status.choices,
        blank=True
    )

    new_status = models.CharField(
        max_length=20,
        choices=Ticket.Status.choices,
        blank=True
    )
    comment = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Ticket history'
        verbose_name_plural = 'Ticket histories'

    def __str__(self):
        return f'{self.ticket.title}: {self.event_type}'


class TicketComment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='ticket_comments',
        null=True,
        blank=True
    )
    text = models.TextField()
    is_internal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket comment'
        verbose_name_plural = 'Ticket comments'

    def __str__(self):
        return f'Comment for ticket #{self.ticket_id}'