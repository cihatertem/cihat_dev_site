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


class TestCihatDevUrls(TestCase):
    def test_debug_urls_appended(self):
        import importlib

        from django.test import override_settings

        import cihat_dev.urls

        # Ensure we start with DEBUG=False to get the base length
        with override_settings(DEBUG=False):
            importlib.reload(cihat_dev.urls)
            initial_len = len(cihat_dev.urls.urlpatterns)

        try:
            with override_settings(DEBUG=True):
                importlib.reload(cihat_dev.urls)
                new_len = len(cihat_dev.urls.urlpatterns)

                self.assertGreater(new_len, initial_len)

                url_patterns_str = [str(p) for p in cihat_dev.urls.urlpatterns]
                media_found = any("media" in p for p in url_patterns_str)
                static_found = any("static" in p for p in url_patterns_str)

                self.assertTrue(media_found, "Media URL pattern not found")
                self.assertTrue(static_found, "Static URL pattern not found")
        finally:
            # Restore the original state so we don't break other tests
            with override_settings(DEBUG=False):
                importlib.reload(cihat_dev.urls)
