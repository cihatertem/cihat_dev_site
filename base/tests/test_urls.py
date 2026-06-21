from django.test import TestCase
from django.urls import reverse


class TestUrls(TestCase):
    def test_sitemap_url_resolves(self):
        url = reverse("base:django.contrib.sitemaps.views.sitemap")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_url_resolves(self):
        url = "/robots.txt"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))

    def test_home_url_resolves(self):
        from django.core.cache import cache
        from django.test import override_settings

        from base.models import User

        cache.clear()

        # Create a user to avoid 404 since home view now relies on it
        test_email = "test@example.com"

        User.objects.create_user(
            username="testuser",
            email=test_email,
            password="password123",
        )

        url = reverse("base:home")
        with override_settings(CONTACT_EMAIL=test_email):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
