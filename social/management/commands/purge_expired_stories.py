from django.core.management.base import BaseCommand
from django.utils import timezone

from social.models import Story


class Command(BaseCommand):
    help = "Delete expired local stories and their private image files."

    def handle(self, *args, **options):
        expired = Story.objects.filter(expires_at__lte=timezone.now())
        deleted_count = 0
        for story in expired.iterator():
            story.delete()
            deleted_count += 1
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} expired stories."))
