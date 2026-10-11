from django.db import models
from django.core.exceptions import ValidationError
import os
import json

def validate_file_size_20mb(value):
    """Reject files larger than 20 MB."""
    limit = 20 * 1024 * 1024  # 20 MB in bytes
    if value.size > limit:
        raise ValidationError(
            f'File too large. Max size is 20 MB. Your file: {value.size / 1024 / 1024:.2f} MB'
        )

class PersonalItem(models.Model):
    # Core fields
    name = models.CharField(max_length=255)
    # department = models.CharField(max_length=255, blank=True, null=True)  # REMOVED
    # phone = models.CharField(max_length=50, blank=True, null=True)         # REMOVED
    priority = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    link = models.URLField(blank=True, null=True)
    
    # ✅ NEW FIELDS ADDED
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending')  # Pending, In Progress, Closed
    
    # File handling
    media_file = models.FileField(upload_to='personal_files/', blank=True, null=True)
    is_multiple = models.BooleanField(default=False)
    file_count = models.IntegerField(default=0)
    
    # To-Do specific
    is_completed = models.BooleanField(default=False)
    telegram_files = models.TextField(blank=True, null=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

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

    def delete(self, *args, **kwargs):
        # ✅ 1. Delete all Telegram files
        try:
            from filemanager.telegram_storage import delete_telegram_message
            tg_map = self.get_telegram_map()
            for slot_key, info in tg_map.items():
                if info and info.get('message_id'):
                    delete_telegram_message(info.get('message_id'))
        except Exception:
            pass

        # ✅ 2. Delete all attached legacy local files
        for stored_file in self.stored_files.all():
            stored_file.delete()

        # ✅ 3. Delete the main legacy media_file from disk
        if self.media_file:
            try:
                if os.path.isfile(self.media_file.path):
                    os.remove(self.media_file.path)
            except Exception:
                pass

        # ✅ 4. Finally, delete the item itself
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