from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Story


@receiver(pre_delete, sender=Story)
def remove_story_image_on_delete(sender, instance, **kwargs):
    if instance.image and instance.image.name:
        instance.image.delete(save=False)
