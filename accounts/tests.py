from django.contrib.auth import authenticate
from django.urls import reverse
from django.test import Client, TestCase
from .models import User


class UserModelTests(TestCase):
    def test_email_is_the_normalized_unique_login_identifier(self):
        user = User.objects.create_user("Meeble@example.com", "safe demo password")

        self.assertEqual(user.email, "meeble@example.com")
        self.assertNotEqual(user.password, "safe demo password")
        self.assertTrue(user.check_password("safe demo password"))
        self.assertEqual(
            authenticate(email="meeble@example.com", password="safe demo password"), user
        )

    def test_user_creation_requires_an_email(self):
        with self.assertRaisesMessage(ValueError, "An email address is required."):
            User.objects.create_user("", "safe demo password")

    def test_registration_hashes_password_and_starts_a_session(self):
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
        self.assertRedirects(response, reverse("home"))
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
