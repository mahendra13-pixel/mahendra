# inventory/signals.py
import logging
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import InventoryItem

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=InventoryItem)
def delete_inventory_image_from_disk(sender, instance, **kwargs):
    """
    Delete the physical image file from disk when an InventoryItem is deleted.
    Fires on single deletes, bulk queryset deletes, AND cascades from Category.delete().
    """
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            logger.warning(f"Failed to delete image for InventoryItem#{instance.pk}: {e}")