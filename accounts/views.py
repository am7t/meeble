from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_http_methods, require_POST
from .forms import EmailAuthenticationForm, ProfileEditForm, RegistrationForm
from .tokens import email_verification_token


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
        uidb64 = urlsafe_base64_encode(str(user.pk).encode())
        token = email_verification_token.make_token(user)
        verification_url = request.build_absolute_uri(
            reverse("accounts:verify_email", kwargs={"uidb64": uidb64, "token": token})
        )
        send_mail(
            "Verify your Meeble email address",
            render_to_string(
                "accounts/email_verification_email.txt", {"verification_url": verification_url}
            ),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return redirect("accounts:verification_sent")
    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def sign_in(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("home")
    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def verify_email(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
    except (TypeError, ValueError, OverflowError):
        user_id = None
    user = get_user_model().objects.filter(pk=user_id).first() if user_id else None
    valid_link = bool(
        user and not user.is_active and email_verification_token.check_token(user, token)
    )
    if request.method == "POST" and valid_link:
        user.is_active = True
        user.save(update_fields=["is_active"])
        return render(request, "accounts/verification_complete.html")
    return render(request, "accounts/verification_confirm.html", {"valid_link": valid_link})


@require_http_methods(["GET"])
def verification_sent(request):
    return render(request, "accounts/verification_sent.html")


@require_POST
def sign_out(request):
    logout(request)
    return redirect("home")


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def profile_edit(request):
    profile = request.user.profile
    form = ProfileEditForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error("handle", "That handle is already in use. Try another one.")
        else:
            messages.success(request, "Your profile changes are saved on this device.")
            return redirect("accounts:profile")
    return render(request, "accounts/profile_edit.html", {"form": form, "profile": profile})
