from django.contrib.auth import authenticate
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.test import Client, TestCase
from .models import User
from .tokens import email_verification_token


class UserModelTests(TestCase):
    def test_email_is_the_normalized_unique_login_identifier(self):
        user = User.objects.create_user("Meeble@example.com", "safe demo password")

        self.assertEqual(user.email, "meeble@example.com")
        self.assertNotEqual(user.password, "safe demo password")
        self.assertTrue(user.check_password("safe demo password"))
        self.assertEqual(
            authenticate(email="meeble@example.com", password="safe demo password"), user
        )
        self.assertEqual(user.profile.handle, f"m_{user.pk}")

    def test_user_creation_requires_an_email(self):
        with self.assertRaisesMessage(ValueError, "An email address is required."):
            User.objects.create_user("", "safe demo password")

    def test_registration_creates_an_inactive_account_until_email_is_verified(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(
                reverse("accounts:register"),
                {
                    "email": "Amelia@example.com",
                    "password1": "CiderMoon!56Little",
                    "password2": "CiderMoon!56Little",
                },
            )

        user = User.objects.get(email="amelia@example.com")
        self.assertNotEqual(user.password, "CiderMoon!56Little")
        self.assertTrue(user.check_password("CiderMoon!56Little"))
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.handle, f"m_{user.pk}")
        self.assertEqual(user.profile.display_name, "Amelia")
        self.assertRedirects(response, reverse("accounts:verification_sent"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("one-time link", mail.outbox[0].body)

        verification_link = next(
            line.strip()
            for line in mail.outbox[0].body.splitlines()
            if line.startswith("http://testserver/")
        )
        verification_path = verification_link.removeprefix("http://testserver")
        confirmation = self.client.get(verification_path)
        self.assertContains(confirmation, "Opening this page does not activate it")
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        verified = self.client.post(verification_path)
        self.assertContains(verified, "Your email is verified.")
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertContains(self.client.get(verification_path), "That link has expired.")

        signed_in = self.client.post(
            reverse("accounts:login"),
            {"username": user.email, "password": "CiderMoon!56Little"},
        )
        self.assertRedirects(signed_in, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_rejects_mismatched_and_weak_passwords(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "amelia@example.com",
                "password1": "password",
                "password2": "different",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="amelia@example.com").exists())
        self.assertContains(response, "Those passwords did not match.")

    def test_login_is_case_insensitive_and_logout_requires_post(self):
        user = User.objects.create_user("amelia@example.com", "CiderMoon!56Little")
        failed = self.client.post(
            reverse("accounts:login"),
            {
                "username": "AMELIA@EXAMPLE.COM",
                "password": "incorrect password",
            },
        )
        self.assertEqual(failed.status_code, 200)
        self.assertContains(failed, "That email address or password doesn’t look right. Try again.")
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "AMELIA@EXAMPLE.COM",
                "password": "CiderMoon!56Little",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("accounts:logout")), reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_auth_forms_reject_post_without_csrf_token(self):
        client = Client(enforce_csrf_checks=True)

        self.assertEqual(client.get(reverse("accounts:register")).status_code, 200)
        response = client.post(
            reverse("accounts:register"),
            {
                "email": "amelia@example.com",
                "password1": "CiderMoon!56Little",
                "password2": "CiderMoon!56Little",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(email="amelia@example.com").exists())

    def test_password_reset_uses_one_time_local_email_link_without_account_enumeration(self):
        user = User.objects.create_user("amelia@example.com", "CiderMoon!56Little")
        reset_url = reverse("accounts:password_reset")
        self.assertContains(self.client.get(reset_url), "Forgot your password?")
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            known = self.client.post(reset_url, {"email": user.email})
            unknown = self.client.post(reset_url, {"email": "nobody@example.com"})

        self.assertRedirects(known, reverse("accounts:password_reset_done"))
        self.assertRedirects(unknown, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("one-time link", mail.outbox[0].body)
        self.assertIn("http://testserver/accounts/password-reset/", mail.outbox[0].body)
        self.assertIn("within one hour", mail.outbox[0].body)

    def test_password_reset_changes_password_and_invalidates_the_link(self):
        user = User.objects.create_user("amelia@example.com", "CiderMoon!56Little")
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            self.client.post(reverse("accounts:password_reset"), {"email": user.email})

        link = next(
            line.strip()
            for line in mail.outbox[0].body.splitlines()
            if line.startswith("http://testserver/")
        )
        link_path = link.removeprefix("http://testserver")
        response = self.client.get(link_path)
        self.assertEqual(response.status_code, 302)
        confirm_path = response.url
        self.assertContains(self.client.get(confirm_path), "Choose a new password.")

        changed = self.client.post(
            confirm_path,
            {"new_password1": "NewCiderMoon!62Set", "new_password2": "NewCiderMoon!62Set"},
        )

        self.assertRedirects(changed, reverse("accounts:password_reset_complete"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewCiderMoon!62Set"))
        self.assertFalse(user.check_password("CiderMoon!56Little"))
        self.assertContains(self.client.get(link_path), "That link has expired.")
        self.assertEqual(
            self.client.post(
                reverse("accounts:login"),
                {"username": user.email, "password": "NewCiderMoon!62Set"},
            ).status_code,
            302,
        )

    def test_password_reset_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(reverse("accounts:password_reset"), {"email": "test@example.com"})

        self.assertEqual(response.status_code, 403)

    def test_account_pages_describe_the_configured_email_backend(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            self.assertContains(
                self.client.get(reverse("accounts:login")), "Reset links are sent by email."
            )
            self.assertContains(
                self.client.get(reverse("accounts:register")),
                "You’ll receive a verification link by email.",
            )
            self.assertContains(
                self.client.get(reverse("accounts:password_reset")),
                "send a one-time reset link by email",
            )

    def test_email_verification_requires_csrf_and_expires_after_one_hour(self):
        user = User.objects.create_user(
            "pending@example.com", "CiderMoon!56Little", is_active=False
        )
        uidb64 = urlsafe_base64_encode(str(user.pk).encode())
        token = email_verification_token.make_token(user)
        verify_url = reverse("accounts:verify_email", kwargs={"uidb64": uidb64, "token": token})
        client = Client(enforce_csrf_checks=True)
        self.assertContains(client.get(verify_url), "Confirm your email address")
        rejected = client.post(verify_url)
        self.assertEqual(rejected.status_code, 403)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        with self.settings(PASSWORD_RESET_TIMEOUT=-1):
            expired = self.client.get(verify_url)
        self.assertContains(expired, "That link has expired.")
        user.refresh_from_db()
        self.assertFalse(user.is_active)


class ProfileEditViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amelia@example.com", "safe demo password")
        self.other_user = User.objects.create_user("jules@example.com", "safe demo password")
        self.url = reverse("accounts:profile")

    def test_profile_editor_requires_a_signed_in_user(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_signed_in_user_can_open_their_profile_editor_from_home(self):
        self.client.force_login(self.user)

        home = self.client.get(reverse("home"))
        editor = self.client.get(self.url)

        self.assertContains(home, f'href="{self.url}"')
        self.assertEqual(editor.status_code, 200)
        self.assertContains(editor, "Edit your profile")
        self.assertContains(
            editor,
            f'href="{reverse("public-profile", kwargs={"handle": self.user.profile.handle})}"',
        )
        self.assertContains(editor, "Color mood")
        self.assertContains(editor, self.user.profile.display_name)
        self.assertNotContains(editor, self.other_user.email)

    def test_signed_in_user_can_edit_only_their_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "handle": "Amelia_Rose",
                "display_name": "Amelia Rose",
                "bio": "Collecting little moments.",
                "theme": "blush",
                "layout": "airy",
                "user": self.other_user.pk,
                "profile_id": self.other_user.profile.pk,
            },
        )

        self.assertRedirects(response, self.url)
        self.user.profile.refresh_from_db()
        self.other_user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.handle, "amelia_rose")
        self.assertEqual(self.user.profile.display_name, "Amelia Rose")
        self.assertEqual(self.user.profile.bio, "Collecting little moments.")
        self.assertEqual(self.user.profile.customization, {"theme": "blush", "layout": "airy"})
        self.assertEqual(self.user.profile.user_id, self.user.pk)
        self.assertEqual(self.other_user.profile.handle, f"m_{self.other_user.pk}")

    def test_invalid_handle_or_customization_is_not_saved(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "handle": self.other_user.profile.handle.upper(),
                "display_name": "Amelia Rose",
                "bio": "",
                "theme": "moss",
                "layout": "cozy",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["handle"])
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.handle, f"m_{self.user.pk}")

        response = self.client.post(
            self.url,
            {
                "handle": f"m_{self.user.pk}",
                "display_name": "Amelia Rose",
                "bio": "",
                "theme": "rainbow",
                "layout": "cozy",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["theme"])
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.customization, {"theme": "moss", "layout": "cozy"})

    def test_profile_page_escapes_saved_user_text(self):
        self.user.profile.bio = '<script>alert("hi")</script>'
        self.user.profile.save()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertContains(response, "&lt;script&gt;alert(&quot;hi&quot;)&lt;/script&gt;")

    def test_profile_updates_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(
            self.url,
            {
                "handle": f"m_{self.user.pk}",
                "display_name": "Amelia",
                "bio": "",
                "theme": "moss",
                "layout": "cozy",
            },
        )

        self.assertEqual(response.status_code, 403)
