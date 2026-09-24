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
