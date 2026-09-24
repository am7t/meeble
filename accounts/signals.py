from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=get_user_model())
def create_profile_for_new_user(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        email_name = instance.email.partition("@")[0]
        Profile.objects.create(
            user=instance,
            handle=f"m_{instance.pk}",
            display_name=email_name.replace(".", " ").replace("_", " ").title()[:40],
        )
