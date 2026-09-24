from django.conf import settings


def email_delivery(request):
    """Tell account screens whether email is printed locally or delivered."""
    return {
        "console_email": settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"
    }
