import os
import json 
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

def validate_file_size_20mb(value):
    limit = 20 * 1024 * 1024  # 20 MB in bytes
    if value.size > limit:
        raise ValidationError(f'File too large. Max size is 20 MB. Your file: {value.size / 1024 / 1024:.2f} MB')

class Contact(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),  # Changed from 'Critical' to 'Urgent'
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Closed', 'Closed'),  # Removed 'Resolved'
    ]
    
    # Staff choices for dropdown
    STAFF_CHOICES = [
        ('Mahendra Kunwar', 'Mahendra Kunwar'),
        ('Ram Kumar Badal', 'Ram Kumar Badal'),
        ('Binaya Kunwar', 'Binaya Kunwar'),
        ('Subash Dahal', 'Subash Dahal'),
        ('Ashish Adhikari', 'Ashish Adhikari'),
    ]
    
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=200, default="General")
    phone = models.CharField(max_length=20, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    os_info = models.CharField(max_length=100, blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium', blank=True, null=True)
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    time = models.TimeField(auto_now_add=True, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    media_file = models.FileField(upload_to='media_files/', null=True, blank=True, validators=[validate_file_size_20mb], verbose_name="Media File (Image/Video)")
    telegram_files = models.TextField(blank=True, null=True, default='')
    is_public = models.BooleanField(default=False)
    
    # NEW FIELDS: Track single vs multiple files
    is_multiple = models.BooleanField(default=False)  # True if multiple files uploaded
    file_count = models.IntegerField(default=0)       # Number of files uploaded
    
    # Multi-select fields (stores comma-separated values)
    call_attended_by = models.CharField(max_length=255, blank=True, null=True)
    handover_to = models.CharField(max_length=255, blank=True, null=True)
    solved_by = models.CharField(max_length=255, blank=True, null=True)
    
    # NEW FIELDS: Assigned To and Remarks
    assigned_to = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_resolved = models.BooleanField(default=False)
    
    # Timestamps for tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)  # NEW: For store form
    link = models.URLField(blank=True, null=True) 
    is_stored = models.BooleanField(default=False)
    stored_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'auth.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='created_issues',
        help_text="User account that submitted this issue"
    )

    def __str__(self):
        return f"{self.name} - {self.department}"

    def mark_as_resolved(self):
        self.is_resolved = True
        self.status = 'Closed' 
        self.resolved_at = timezone.now()
        self.save()
        
    def get_telegram_map(self):
        """Parse telegram_files JSON or return empty dict."""
        if not self.telegram_files:
            return {}
        try:
            return json.loads(self.telegram_files)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_telegram_file(self, slot_key, info):
        """Save a Telegram file entry for a slot."""
        data = self.get_telegram_map()
        data[slot_key] = info
        self.telegram_files = json.dumps(data)

    def remove_telegram_file(self, slot_key):
        """Remove a slot from the Telegram map."""
        data = self.get_telegram_map()
        data.pop(slot_key, None)
        self.telegram_files = json.dumps(data)
    
        # ✅ NEW: Delete Telegram files when Contact is deleted
    def delete(self, *args, **kwargs):
        # 1. Delete all Telegram files
        try:
            from filemanager.telegram_storage import delete_telegram_message
            for slot_key, info in self.get_telegram_map().items():
                if info and info.get('message_id'):
                    delete_telegram_message(info.get('message_id'))
        except Exception:
            pass

        # 2. Delete all legacy local StoredFile rows (and their disk files)
        for stored_file in self.stored_files.all():
            stored_file.delete()

        # 3. Delete the legacy media_file from disk
        if self.media_file:
            try:
                if os.path.isfile(self.media_file.path):
                    os.remove(self.media_file.path)
            except Exception:
                pass

        # 4. Finally, delete the Contact itself
        super().delete(*args, **kwargs)

class StoredFile(models.Model):
    """Individual files for stored items"""
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE, related_name='stored_files')
    file = models.FileField(upload_to='stored_files/', validators=[validate_file_size_20mb])
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file_name    
    
    def delete(self, *args, **kwargs):
        if self.file:
            try:
                if os.path.isfile(self.file.path):
                    os.remove(self.file.path)
            except Exception:
                pass
        super().delete(*args, **kwargs)    