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

class LinkCard(models.Model):
    # Card-level: only name
    name = models.CharField(max_length=255)

    # ============ SLOT 1 ============
    link_name_1 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_1 = models.TextField(blank=True, null=True)
    link_url_1  = models.URLField(blank=True, null=True)
    link_file_1   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_1_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_1_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_1_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 2 ============
    link_name_2 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_2 = models.TextField(blank=True, null=True)
    link_url_2  = models.URLField(blank=True, null=True)
    link_file_2   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_2_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_2_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_2_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 3 ============
    link_name_3 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_3 = models.TextField(blank=True, null=True)
    link_url_3  = models.URLField(blank=True, null=True)
    link_file_3   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_3_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_3_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_3_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 4 ============
    link_name_4 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_4 = models.TextField(blank=True, null=True)
    link_url_4  = models.URLField(blank=True, null=True)
    link_file_4   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_4_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_4_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_4_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 5 ============
    link_name_5 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_5 = models.TextField(blank=True, null=True)
    link_url_5  = models.URLField(blank=True, null=True)
    link_file_5   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_5_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_5_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_5_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 6 ============
    link_name_6 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_6 = models.TextField(blank=True, null=True)
    link_url_6  = models.URLField(blank=True, null=True)
    link_file_6   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_6_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_6_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_6_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 7 ============
    link_name_7 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_7 = models.TextField(blank=True, null=True)
    link_url_7  = models.URLField(blank=True, null=True)
    link_file_7   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_7_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_7_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_7_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 8 ============
    link_name_8 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_8 = models.TextField(blank=True, null=True)
    link_url_8  = models.URLField(blank=True, null=True)
    link_file_8   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_8_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_8_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_8_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])

    # ============ SLOT 9 ============
    link_name_9 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_9 = models.TextField(blank=True, null=True)
    link_url_9  = models.URLField(blank=True, null=True)
    link_file_9   = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_9_b = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_9_c = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    link_file_9_d = models.FileField(upload_to='link_files/', blank=True, null=True, validators=[validate_file_size_20mb])
    
    telegram_files = models.TextField(blank=True, null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def link_count(self):
        tg_map = self.get_telegram_map()
        count = 0
        for i in range(1, 10):
            has_text = (
                getattr(self, f'link_name_{i}')
                or getattr(self, f'link_desc_{i}')
                or getattr(self, f'link_url_{i}')
            )
            has_file = any(f"{i}{suffix}" in tg_map for suffix in ['', '_b', '_c', '_d'])
            if has_text or has_file:
                count += 1
        return count

    def filled_slots(self):
        """Return list of dicts for only the filled slots (Telegram-backed)."""
        tg_map = self.get_telegram_map()
        slots = []
        for i in range(1, 10):
            name = getattr(self, f'link_name_{i}')
            desc = getattr(self, f'link_desc_{i}')
            url  = getattr(self, f'link_url_{i}')

            files = []
            for suffix in ['', '_b', '_c', '_d']:
                slot_key = f"{i}{suffix}"
                info = tg_map.get(slot_key)
                if info:
                    files.append({
                        'slot_key': slot_key,
                        'name': info.get('file_name', 'file'),
                        'size': info.get('file_size', 0),
                        'suffix': suffix,
                    })

            if name or desc or url or files:
                slots.append({
                    'index': i,
                    'name': name,
                    'desc': desc,
                    'url': url,
                    'files': files,
                })
        return slots
    
    def get_telegram_map(self):
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
        try:
            from filemanager.telegram_storage import delete_telegram_message
            tg_map = self.get_telegram_map()
            for slot_key, info in tg_map.items():
                if info and info.get('message_id'):
                    delete_telegram_message(info.get('message_id'))
        except Exception:
            pass

        
        for i in range(1, 10):
            for suffix in ['', '_b', '_c', '_d']:
                f = getattr(self, f'link_file_{i}{suffix}', None)
                if f:
                    try:
                        if os.path.isfile(f.path):
                            os.remove(f.path)
                    except Exception:
                        pass

        super().delete(*args, **kwargs)