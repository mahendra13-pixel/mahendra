from django.db import models
from django.conf import settings


class ZipUpload(models.Model):
    """Tracks one folder→zip upload and its extraction."""

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('extracted', 'Extracted'),
        ('failed',    'Failed'),
    ]

    # Where it was uploaded from ("issue" or "store")
    source = models.CharField(max_length=20)

    # The ID of the related object (issue id / store id)
    source_id = models.CharField(max_length=64, blank=True, default='')

    original_name = models.CharField(max_length=255, blank=True, default='')
    zip_size = models.BigIntegerField(default=0)
    extracted_path = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, default='')

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source}#{self.source_id} — {self.original_name} [{self.status}]"