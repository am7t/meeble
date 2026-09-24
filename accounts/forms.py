from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User


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
