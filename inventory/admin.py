# from django.contrib import admin

# Register your models here.
# inventory/admin.py
# inventory/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, InventoryItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'item_count', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def item_count(self, obj):
        """Display number of items in category"""
        count = obj.items.count()
        return format_html('<span class="badge bg-info">{}</span>', count)
    item_count.short_description = 'Items Count'
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = [
        'thumbnail_preview', 
        'name', 
        'category', 
        'model', 
        'status_badge', 
        'quantity',
        'media_type_icon',
        'file_size_display',
        'created_at'
    ]
    
    list_filter = ['category', 'status', 'media_type', 'created_at']
    search_fields = ['name', 'model', 'specification', 'remarks', 'original_filename']
    readonly_fields = [
        'media_type', 
        'original_filename', 
        'file_size_mb', 
        'created_at', 
        'updated_at',
        'preview_media'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'model', 'status', 'quantity')
        }),
        ('Media', {
            'fields': ('image', 'preview_media', 'media_type', 'original_filename', 'file_size_mb'),
            'description': 'Upload images (jpg, png, gif, webp), videos (mp4, webm, ogg), or audio files (mp3, wav). Max size: 50MB'
        }),
        ('Specifications', {
            'fields': ('specification', 'remarks')
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Display thumbnail in list view"""
        if not obj.image or not obj.image.url:
            return format_html('<span class="text-muted">📷 No Media</span>')
        
        url = obj.image.url
        
        if obj.media_type == 'video':
            return format_html('''
                <video style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" muted>
                    <source src="{}" type="video/mp4">
                </video>
            ''', url)
        elif obj.media_type == 'image':
            return format_html('''
                <img src="{}" alt="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">
            ''', url, obj.name)
        elif obj.media_type == 'audio':
            return format_html('''
                <div style="width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; background: #f8f9fa; border-radius: 4px;">
                    <i class="fas fa-music fa-2x text-primary"></i>
                </div>
            ''')
        else:
            return format_html('''
                <div style="width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; background: #f8f9fa; border-radius: 4px;">
                    <i class="fas fa-file fa-2x text-muted"></i>
                </div>
            ''')
    thumbnail_preview.short_description = 'Media'
    thumbnail_preview.allow_tags = True
    
    def preview_media(self, obj):
        """Display full media preview in detail view"""
        if not obj.image or not obj.image.url:
            return format_html('<div class="alert alert-info">No media uploaded</div>')
        
        url = obj.image.url
        
        if obj.media_type == 'video':
            return format_html('''
                <div style="background: #000; padding: 10px; border-radius: 8px; max-width: 500px;">
                    <video controls style="width: 100%; max-height: 400px; border-radius: 4px;">
                        <source src="{}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                    <div style="color: #fff; padding: 5px; font-size: 12px; text-align: center; margin-top: 5px;">
                        <i class="fas fa-video"></i> {} ({})
                    </div>
                </div>
            ''', url, obj.original_filename or obj.image.name, obj.get_file_size_display())
        elif obj.media_type == 'audio':
            return format_html('''
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; max-width: 500px;">
                    <div style="text-align: center; margin-bottom: 15px;">
                        <i class="fas fa-music fa-3x text-primary"></i>
                    </div>
                    <audio controls style="width: 100%;">
                        <source src="{}" type="audio/mpeg">
                        Your browser does not support the audio tag.
                    </audio>
                    <div style="padding: 5px; font-size: 12px; text-align: center; margin-top: 5px;">
                        <i class="fas fa-headphones"></i> {} ({})
                    </div>
                </div>
            ''', url, obj.original_filename or obj.image.name, obj.get_file_size_display())
        elif obj.media_type == 'image':
            return format_html('''
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; max-width: 500px;">
                    <img src="{}" alt="{}" style="max-width: 100%; max-height: 400px; border-radius: 4px; object-fit: contain;">
                    <div style="padding: 5px; font-size: 12px; text-align: center; margin-top: 5px;">
                        <i class="fas fa-image"></i> {} ({})
                    </div>
                </div>
            ''', url, obj.name, obj.original_filename or obj.image.name, obj.get_file_size_display())
        else:
            return format_html('''
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                    <i class="fas fa-file fa-4x text-muted"></i>
                    <p><strong>{}</strong></p>
                    <p class="text-muted">Size: {}</p>
                    <a href="{}" target="_blank" class="btn btn-sm btn-primary">
                        <i class="fas fa-download"></i> Download
                    </a>
                </div>
            ''', obj.original_filename or obj.image.name, obj.get_file_size_display(), url)
    preview_media.short_description = 'Media Preview'
    preview_media.allow_tags = True
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'working': 'success',
            'not_working': 'danger',
            'repair': 'warning',
            'disposed': 'secondary'
        }
        icons = {
            'working': '✅',
            'not_working': '❌',
            'repair': '🔧',
            'disposed': '🗑️'
        }
        color = colors.get(obj.status, 'secondary')
        icon = icons.get(obj.status, '')
        return format_html(
            '<span class="badge bg-{}">{}</span>', 
            color, 
            f"{icon} {obj.get_status_display()}"
        )
    status_badge.short_description = 'Status'
    status_badge.allow_tags = True
    
    def media_type_icon(self, obj):
        """Display media type with icon"""
        icons = {
            'image': '🖼️',
            'video': '🎬',
            'audio': '🎵',
            'other': '📄',
            'none': '📷'
        }
        labels = {
            'image': 'Image',
            'video': 'Video',
            'audio': 'Audio',
            'other': 'Other',
            'none': 'None'
        }
        icon = icons.get(obj.media_type, '📄')
        label = labels.get(obj.media_type, 'Unknown')
        return format_html('{} {}', icon, label)
    media_type_icon.short_description = 'Media Type'
    media_type_icon.allow_tags = True
    
    def file_size_display(self, obj):
        """Display file size"""
        if obj.file_size_mb:
            if obj.file_size_mb >= 1024:
                return f"{obj.file_size_mb / 1024:.2f} GB"
            else:
                return f"{obj.file_size_mb:.2f} MB"
        return '-'
    file_size_display.short_description = 'File Size'
    
    def get_actions(self, request):
        """Custom actions for bulk operations"""
        actions = super().get_actions(request)
        # Add custom actions if needed
        return actions
    
    actions = ['mark_as_working', 'mark_as_not_working', 'mark_as_repair', 'mark_as_disposed']
    
    def mark_as_working(self, request, queryset):
        """Bulk mark items as working"""
        updated = queryset.update(status='working')
        self.message_user(request, f'{updated} items marked as Working.')
    mark_as_working.short_description = "Mark selected as Working"
    
    def mark_as_not_working(self, request, queryset):
        """Bulk mark items as not working"""
        updated = queryset.update(status='not_working')
        self.message_user(request, f'{updated} items marked as Not Working.')
    mark_as_not_working.short_description = "Mark selected as Not Working"
    
    def mark_as_repair(self, request, queryset):
        """Bulk mark items as under repair"""
        updated = queryset.update(status='repair')
        self.message_user(request, f'{updated} items marked as Under Repair.')
    mark_as_repair.short_description = "Mark selected as Under Repair"
    
    def mark_as_disposed(self, request, queryset):
        """Bulk mark items as disposed"""
        updated = queryset.update(status='disposed')
        self.message_user(request, f'{updated} items marked as Disposed.')
    mark_as_disposed.short_description = "Mark selected as Disposed"
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on creation"""
        if not change:  # New object
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)


# Optional: Custom inline admin for Category to show items
class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    fields = ['name', 'model', 'status', 'quantity', 'media_type_icon']
    readonly_fields = ['media_type_icon']
    extra = 0
    max_num = 10
    show_change_link = True
    
    def media_type_icon(self, obj):
        """Display media type icon in inline"""
        icons = {
            'image': '🖼️',
            'video': '🎬',
            'audio': '🎵',
            'other': '📄',
            'none': '📷'
        }
        return icons.get(obj.media_type, '📄')
    media_type_icon.short_description = 'Media'


# Update CategoryAdmin to include inline items
class EnhancedCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'item_count', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [InventoryItemInline]
    
    def item_count(self, obj):
        """Display number of items in category"""
        count = obj.items.count()
        return format_html('<span class="badge bg-info">{}</span>', count)
    item_count.short_description = 'Items Count'
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Re-register with enhanced admin
admin.site.unregister(Category)
admin.site.register(Category, EnhancedCategoryAdmin)