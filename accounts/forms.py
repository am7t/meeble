from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    PROFILE_LAYOUT_CHOICES,
    PROFILE_THEME_CHOICES,
    Profile,
    User,
    validate_profile_customization,
)


class EmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": _("That email address or password doesn’t look right. Try again.")
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email address"
        self.fields["username"].widget = forms.EmailInput(
            attrs={"autocomplete": "username", "autofocus": True}
        )

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("email",)
        widgets = {"email": forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True})}

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password1")
        confirmation = cleaned.get("password2")
        if password and confirmation and password != confirmation:
            self.add_error("password2", "Those passwords did not match.")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    theme = forms.ChoiceField(label="Color mood", choices=PROFILE_THEME_CHOICES)
    layout = forms.ChoiceField(label="Profile feel", choices=PROFILE_LAYOUT_CHOICES)

    class Meta:
        model = Profile
        fields = ("handle", "display_name", "bio")
        widgets = {
            "handle": forms.TextInput(attrs={"autocomplete": "nickname", "maxlength": 24}),
            "display_name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 40}),
            "bio": forms.Textarea(attrs={"rows": 3, "maxlength": 160}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        customization = self.instance.customization or {}
        self.fields["theme"].initial = customization.get("theme", "moss")
        self.fields["layout"].initial = customization.get("layout", "cozy")
        self.fields["handle"].help_text = "Use 3–24 letters, numbers, or underscores."
        self.fields["bio"].help_text = "Up to 160 characters."

    def clean_handle(self):
        handle = self.cleaned_data["handle"].strip().lower()
        conflicts = Profile.objects.filter(handle__iexact=handle).exclude(pk=self.instance.pk)
        if conflicts.exists():
            raise ValidationError("That handle is already in use. Try another one.")
        return handle

    def clean(self):
        cleaned = super().clean()
        if "theme" in cleaned and "layout" in cleaned:
            try:
                validate_profile_customization(
                    {"theme": cleaned["theme"], "layout": cleaned["layout"]}
                )
            except ValidationError as error:
                self.add_error(None, error)
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.customization = {
            "theme": self.cleaned_data["theme"],
            "layout": self.cleaned_data["layout"],
        }
        if commit:
            profile.save()
        return profile
