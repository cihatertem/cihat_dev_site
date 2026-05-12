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
        url = reverse("base:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
