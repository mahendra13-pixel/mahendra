from django.db import models
import os


class LinkCard(models.Model):
    # Card-level: only name
    name = models.CharField(max_length=255)

    # 9 rows — each has its own name, description, url, file
    link_name_1 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_1 = models.TextField(blank=True, null=True)
    link_url_1 = models.URLField(blank=True, null=True)
    link_file_1 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_2 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_2 = models.TextField(blank=True, null=True)
    link_url_2 = models.URLField(blank=True, null=True)
    link_file_2 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_3 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_3 = models.TextField(blank=True, null=True)
    link_url_3 = models.URLField(blank=True, null=True)
    link_file_3 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_4 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_4 = models.TextField(blank=True, null=True)
    link_url_4 = models.URLField(blank=True, null=True)
    link_file_4 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_5 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_5 = models.TextField(blank=True, null=True)
    link_url_5 = models.URLField(blank=True, null=True)
    link_file_5 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_6 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_6 = models.TextField(blank=True, null=True)
    link_url_6 = models.URLField(blank=True, null=True)
    link_file_6 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_7 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_7 = models.TextField(blank=True, null=True)
    link_url_7 = models.URLField(blank=True, null=True)
    link_file_7 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_8 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_8 = models.TextField(blank=True, null=True)
    link_url_8 = models.URLField(blank=True, null=True)
    link_file_8 = models.FileField(upload_to='link_files/', blank=True, null=True)

    link_name_9 = models.CharField(max_length=255, blank=True, null=True)
    link_desc_9 = models.TextField(blank=True, null=True)
    link_url_9 = models.URLField(blank=True, null=True)
    link_file_9 = models.FileField(upload_to='link_files/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def link_count(self):
        count = 0
        for i in range(1, 10):
            if (getattr(self, f'link_name_{i}')
                    or getattr(self, f'link_desc_{i}')
                    or getattr(self, f'link_url_{i}')
                    or getattr(self, f'link_file_{i}')):
                count += 1
        return count

    def filled_slots(self):
        """Return list of dicts for only the filled slots."""
        slots = []
        for i in range(1, 10):
            name = getattr(self, f'link_name_{i}')
            desc = getattr(self, f'link_desc_{i}')
            url = getattr(self, f'link_url_{i}')
            file = getattr(self, f'link_file_{i}')
            if name or desc or url or file:
                slots.append({
                    'index': i,
                    'name': name,
                    'desc': desc,
                    'url': url,
                    'file': file,
                })
        return slots

    def delete(self, *args, **kwargs):
        for i in range(1, 10):
            f = getattr(self, f'link_file_{i}', None)
            if f:
                try:
                    if os.path.isfile(f.path):
                        os.remove(f.path)
                except Exception:
                    pass
        super().delete(*args, **kwargs)