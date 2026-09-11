from django.db import models

class Visit(models.Model):
    """Records every visit to the site"""
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)
    os_info = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    path = models.CharField(max_length=500, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    is_authenticated = models.BooleanField(default=False)
    referer = models.CharField(max_length=500, blank=True, null=True)
    session_key = models.CharField(max_length=100, blank=True, null=True)
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visited_at']
        verbose_name = "Visit"
        verbose_name_plural = "Visits"

    def __str__(self):
        return f"{self.ip_address} - {self.username or 'Anonymous'} - {self.visited_at}"