import os
from django.db import models
from django.utils import timezone

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
    media_file = models.FileField(upload_to='media_files/', null=True, blank=True, verbose_name="Media File (Image/Video)")
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
        """Mark the issue as resolved and set resolved_at timestamp"""
        self.is_resolved = True
        self.status = 'Closed'  # Changed from 'Resolved' to 'Closed'
        self.resolved_at = timezone.now()
        self.save()

class StoredFile(models.Model):
    """Individual files for stored items"""
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE, related_name='stored_files')
    file = models.FileField(upload_to='stored_files/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file_name        