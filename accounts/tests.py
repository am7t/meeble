from django.contrib.auth import authenticate
from django.test import TestCase
from .models import User


class UserModelTests(TestCase):
    def test_email_is_the_normalized_unique_login_identifier(self):
        user = User.objects.create_user("Meeble@example.com", "safe demo password")

        self.assertEqual(user.email, "meeble@example.com")
        self.assertNotEqual(user.password, "safe demo password")
        self.assertTrue(user.check_password("safe demo password"))
        self.assertEqual(authenticate(email="meeble@example.com", password="safe demo password"), user)

    def test_user_creation_requires_an_email(self):
        with self.assertRaisesMessage(ValueError, "An email address is required."):
            User.objects.create_user("", "safe demo password")
