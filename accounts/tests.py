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
        self.assertEqual(user.profile.handle, f"m_{user.pk}")

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
        self.assertEqual(user.profile.handle, f"m_{user.pk}")
        self.assertEqual(user.profile.display_name, "Amelia")
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
