from django.db import models
import os

class PersonalItem(models.Model):
    # Core fields
    name = models.CharField(max_length=255)
    # department = models.CharField(max_length=255, blank=True, null=True)  # REMOVED
    # phone = models.CharField(max_length=50, blank=True, null=True)         # REMOVED
    priority = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # ✅ NEW FIELDS ADDED
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending')  # Pending, In Progress, Closed
    
    # File handling
    media_file = models.FileField(upload_to='personal_files/', blank=True, null=True)
    is_multiple = models.BooleanField(default=False)
    file_count = models.IntegerField(default=0)
    
    # To-Do specific
    is_completed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # ✅ 1. Delete all attached files from disk first
        for stored_file in self.stored_files.all():
            stored_file.delete()

        # ✅ 2. Delete the main media_file from disk
        if self.media_file:
            if os.path.isfile(self.media_file.path):
                os.remove(self.media_file.path)
        
        # ✅ 3. Finally, delete the item itself
        super().delete(*args, **kwargs)


class PersonalStoredFile(models.Model):
    item = models.ForeignKey(PersonalItem, on_delete=models.CASCADE, related_name='stored_files')
    file = models.FileField(upload_to='personal_files/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)

    def delete(self, *args, **kwargs):
        # Hard delete the file from disk
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)