from django.contrib.auth import get_user_model
from django.test import TestCase


class LocalAppViewsTests(TestCase):
    def test_home_serves_the_showcase(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good things happen")
        self.assertContains(response, "/static/web/app.js")

    def test_health_check_reports_local_service(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "meeble-local"})

    def test_signed_in_home_exposes_session_and_csrf_context_to_the_ui(self):
        user = get_user_model().objects.create_user("amelia@example.com", "safe demo password")
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertContains(response, 'data-authenticated="true"')
        self.assertContains(response, 'data-display-name="Amelia"')
        self.assertContains(response, 'name="csrf-token" content="')
        self.assertContains(response, 'feed: "/api/feed/"')
