from django.contrib import admin

from .models import Category, Department, Ticket, TicketHistory


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department')
    list_filter = ('department',)
    search_fields = ('name',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'user',
        'category',
        'department',
        'confidence',
        'status',
        'created_at',
    )
    list_filter = ('status', 'category', 'department')
    search_fields = ('title', 'text', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'old_status', 'new_status', 'changed_at')
    list_filter = ('old_status', 'new_status')
    search_fields = ('ticket__title',)