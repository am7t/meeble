from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Length, Lower
from django.db.models.lookups import GreaterThanOrEqual, LessThanOrEqual


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("A superuser must have staff and superuser privileges.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Local account using email as its unique sign-in identifier."""

    username = None
    email = models.EmailField(unique=True)
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Profile(models.Model):
    """Public profile fields kept separate from authentication credentials."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    handle = models.CharField(
        max_length=24,
        validators=[
            RegexValidator(r"^[a-zA-Z0-9_]{3,24}$", "Use 3–24 letters, numbers, or underscores.")
        ],
    )
    display_name = models.CharField(max_length=40)
    bio = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("handle"), name="profile_handle_ci_unique"),
            models.CheckConstraint(
                condition=GreaterThanOrEqual(Length("handle"), 3)
                & LessThanOrEqual(Length("handle"), 24),
                name="profile_handle_length_valid",
            ),
            models.CheckConstraint(
                condition=GreaterThanOrEqual(Length("display_name"), 1)
                & LessThanOrEqual(Length("display_name"), 40),
                name="profile_display_name_length_valid",
            ),
            models.CheckConstraint(
                condition=Q(bio="") | LessThanOrEqual(Length("bio"), 160),
                name="profile_bio_length_valid",
            ),
        ]
        indexes = [models.Index(fields=["created_at"], name="profile_created_idx")]

    def __str__(self):
        return f"@{self.handle}"
