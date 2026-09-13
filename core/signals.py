import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Contact, StoredFile


@receiver(post_delete, sender=StoredFile)
def delete_storedfile_file_from_disk(sender, instance, **kwargs):
    """
    Delete the physical file from disk when a StoredFile row is deleted.
    Fires on single-instance deletes, bulk queryset deletes, and cascades.
    """
    if instance.file:
        try:
            instance.file.delete(save=False)
        except Exception:
            try:
                full = os.path.join(settings.MEDIA_ROOT, str(instance.file))
                if os.path.exists(full):
                    os.remove(full)
            except Exception:
                pass


@receiver(post_delete, sender=Contact)
def delete_contact_media_file_from_disk(sender, instance, **kwargs):
    """
    Delete the Contact's legacy media_file from disk when a Contact is deleted.
    Redundant with view code, but a safety net.
    """
    if instance.media_file:
        try:
            instance.media_file.delete(save=False)
        except Exception:
            pass