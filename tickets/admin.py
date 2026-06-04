from django.contrib import admin

from tickets.models import (
    Category,
    Company,
    CompanyApiKey,
    Department,
    Source,
    Ticket,
    TicketComment,
    TicketHistory,
    UserProfile,
)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company', 'role', 'is_active', 'created_at')
    list_filter = ('company', 'role', 'is_active')
    search_fields = ('user__username', 'user__email', 'company__name')


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'company',
        'source_type',
        'is_active',
        'created_at',
    )
    list_filter = ('source_type', 'is_active', 'company')
    search_fields = ('name', 'company__name')


@admin.register(CompanyApiKey)
class CompanyApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'company',
        'is_active',
        'created_at',
        'last_used_at',
    )
    list_filter = ('company', 'is_active')
    search_fields = ('name', 'company__name', 'key')
    readonly_fields = ('key', 'created_at', 'last_used_at')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('name', 'company__name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'department', 'is_active')
    list_filter = ('company', 'department', 'is_active')
    search_fields = ('name', 'company__name', 'department__name')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'company',
        'source',
        'category',
        'department',
        'confidence',
        'status',
        'created_at',
    )
    list_filter = (
        'company',
        'source',
        'status',
        'category',
        'department',
    )
    search_fields = (
        'title',
        'text',
        'external_id',
        'author_name',
        'author_email',
        'company__name',
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ticket',
        'changed_by',
        'old_status',
        'new_status',
        'changed_at',
    )
    list_filter = ('old_status', 'new_status', 'changed_by')
    search_fields = ('ticket__title', 'changed_by__username')

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ticket',
        'author',
        'is_internal',
        'created_at',
    )
    list_filter = ('is_internal', 'author')
    search_fields = ('ticket__title', 'text', 'author__username')
    readonly_fields = ('created_at',)