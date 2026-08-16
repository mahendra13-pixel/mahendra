from django.contrib import admin
from .models import Contact
from django.utils import timezone

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    # Fields to display in list view
    list_display = (
        'id',
        'name',
        'department',
        'phone',
        'priority',
        'status',
        'is_resolved',
        'is_stored',
        'created_at',
    )
    
    # Fields to filter by
    list_filter = (
        'priority',
        'status',
        'is_resolved',
        'is_stored',
        'is_public',
        'department',
        'created_at',
    )
    
    # Fields to search
    search_fields = (
        'name',
        'department',
        'phone',
        'message',
        'description',
        'remarks',
        'ip_address',
        'hostname',
        'username',
    )
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Fields to display in detail view
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'department', 'phone', 'priority')
        }),
        ('Client Information', {
            'fields': ('ip_address', 'hostname', 'username', 'os_info')
        }),
        ('Issue Details', {
            'fields': ('message', 'description', 'remarks', 'media_file')
        }),
        ('Staff Assignment', {
            'fields': ('call_attended_by', 'handover_to', 'solved_by', 'assigned_to')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_resolved', 'is_public', 'is_stored')
        }),
        ('File Information', {
            'fields': ('is_multiple', 'file_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at', 'stored_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = (
        'created_at',
        'updated_at',
        'resolved_at',
        'stored_at',
        'date',
        'time',
    )
    
    # Actions
    actions = ['mark_as_resolved', 'mark_as_pending', 'mark_as_stored', 'make_public', 'make_private']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True, status='Closed', resolved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} issues marked as resolved.")
    mark_as_resolved.short_description = "Mark selected issues as Resolved"
    
    def mark_as_pending(self, request, queryset):
        queryset.update(is_resolved=False, status='Pending', resolved_at=None)
        self.message_user(request, f"{queryset.count()} issues marked as Pending.")
    mark_as_pending.short_description = "Mark selected issues as Pending"
    
    def mark_as_stored(self, request, queryset):
        queryset.update(is_stored=True, status='Stored', stored_at=timezone.now())
        self.message_user(request, f"{queryset.count()} issues marked as Stored.")
    mark_as_stored.short_description = "Mark selected issues as Stored"
    
    def make_public(self, request, queryset):
        queryset.update(is_public=True)
        self.message_user(request, f"{queryset.count()} issues marked as Public.")
    make_public.short_description = "Make selected issues Public"
    
    def make_private(self, request, queryset):
        queryset.update(is_public=False)
        self.message_user(request, f"{queryset.count()} issues marked as Private.")
    make_private.short_description = "Make selected issues Private"