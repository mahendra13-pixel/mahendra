from django.db import models

# Create your models here.
# inventory/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Maximum file size (50MB)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB in bytes

def validate_file_size(value):
    """Validate that the file size doesn't exceed 50MB"""
    if value.size > MAX_UPLOAD_SIZE:
        raise ValidationError(f'File size cannot exceed 50MB. Current size: {(value.size / (1024 * 1024)):.2f}MB')

def get_media_type(content_type):
    """Determine media type based on content type"""
    if content_type and content_type.startswith('image/'):
        return 'image'
    elif content_type and content_type.startswith('video/'):
        return 'video'
    elif content_type and content_type.startswith('audio/'):
        return 'audio'
    return 'other'

class Category(models.Model):
    """Category for inventory items (Printers, CPUs, Monitors, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']


class InventoryItem(models.Model):
    """Individual inventory item"""
    
    # Status choices
    STATUS_CHOICES = [
        ('working', 'Working'),
        ('not_working', 'Not Working'),
        ('repair', 'Under Repair'),
        ('disposed', 'Disposed'),
    ]
    
    # Media type choices
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
        ('none', 'No Media'),
    ]
    
    # Basic info
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    model = models.CharField(max_length=200, blank=True, null=True)
    
    # Status and quantity
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='working')
    quantity = models.IntegerField(default=1)
    
    # Specifications
    specification = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    # Media (Image/Video/Audio) with size validation
    image = models.ImageField(
        upload_to='inventory_images/', 
        blank=True, 
        null=True,
        validators=[validate_file_size]
    )
    
    # Media type tracking (auto-detected from uploaded file)
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        default='none',
        blank=True,
        null=True,
        help_text="Type of media uploaded (auto-detected)"
    )
    
    # Original filename for display
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    
    # File size in MB for display
    file_size_mb = models.FloatField(blank=True, null=True, help_text="File size in MB")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        media_icon = '📷' if self.media_type == 'image' else '🎬' if self.media_type == 'video' else '🎵' if self.media_type == 'audio' else '📄'
        return f"{media_icon} {self.category.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-detect media type when image is uploaded
        if self.image and hasattr(self.image, 'file'):
            # Get content type
            content_type = getattr(self.image.file, 'content_type', None)
            if not content_type and hasattr(self.image, 'content_type'):
                content_type = self.image.content_type
            
            # Detect media type
            if content_type:
                self.media_type = get_media_type(content_type)
            elif self.image.name:
                # Fallback: check file extension
                ext = self.image.name.lower().split('.')[-1] if '.' in self.image.name else ''
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico']:
                    self.media_type = 'image'
                elif ext in ['mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv', 'flv', 'wmv']:
                    self.media_type = 'video'
                elif ext in ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a']:
                    self.media_type = 'audio'
                else:
                    self.media_type = 'other'
            
            # Store file size in MB
            self.file_size_mb = round(self.image.size / (1024 * 1024), 2)
            
            # Store original filename
            self.original_filename = self.image.name
        
        super().save(*args, **kwargs)
    
    def get_media_html(self, max_width=300, max_height=200, controls=True):
        """Generate HTML for displaying media based on type"""
        if not self.image or not self.image.url:
            return '<span class="text-muted">No Media</span>'
        
        url = self.image.url
        controls_attr = 'controls' if controls else ''
        
        if self.media_type == 'video':
            return f'''
                <video {controls_attr} style="max-width: {max_width}px; max-height: {max_height}px; border-radius: 4px;">
                    <source src="{url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            '''
        elif self.media_type == 'audio':
            return f'''
                <audio {controls_attr} style="width: 100%; max-width: {max_width}px;">
                    <source src="{url}" type="audio/mpeg">
                    Your browser does not support the audio tag.
                </audio>
            '''
        elif self.media_type == 'image':
            return f'''
                <img src="{url}" alt="{self.name}" style="max-width: {max_width}px; max-height: {max_height}px; border-radius: 4px; object-fit: contain;">
            '''
        else:
            return f'''
                <div class="text-center">
                    <i class="fas fa-file fa-3x text-muted"></i>
                    <br><small class="text-muted">{self.original_filename or 'Unknown file'}</small>
                </div>
            '''
    
    def get_media_thumbnail(self, size=40):
        """Get thumbnail HTML for table view"""
        if not self.image or not self.image.url:
            return '<span class="text-muted">📷</span>'
        
        url = self.image.url
        
        if self.media_type == 'video':
            return f'''
                <video style="width: {size}px; height: {size}px; object-fit: cover; border-radius: 4px;" muted>
                    <source src="{url}" type="video/mp4">
                </video>
            '''
        elif self.media_type == 'image':
            return f'''
                <img src="{url}" alt="{self.name}" style="width: {size}px; height: {size}px; object-fit: cover; border-radius: 4px;">
            '''
        elif self.media_type == 'audio':
            return f'''
                <div style="width: {size}px; height: {size}px; display: flex; align-items: center; justify-content: center; background: #f8f9fa; border-radius: 4px;">
                    <i class="fas fa-music fa-2x text-primary"></i>
                </div>
            '''
        else:
            return f'''
                <div style="width: {size}px; height: {size}px; display: flex; align-items: center; justify-content: center; background: #f8f9fa; border-radius: 4px;">
                    <i class="fas fa-file fa-2x text-muted"></i>
                </div>
            '''
    
    def get_file_size_display(self):
        """Display file size in human readable format"""
        if self.file_size_mb:
            if self.file_size_mb >= 1024:
                return f"{self.file_size_mb / 1024:.2f} GB"
            else:
                return f"{self.file_size_mb:.2f} MB"
        return "-"
    
    class Meta:
        ordering = ['category__name', 'name']