from django.test import TestCase
from django.urls import reverse

from base.sitemaps import BaseSiteMap


class BaseSiteMapTest(TestCase):
    def setUp(self):
        self.sitemap = BaseSiteMap()

    def test_items(self):
        self.assertEqual(self.sitemap.items(), ["base:home"])

    def test_location(self):
        item = "base:home"
        self.assertEqual(self.sitemap.location(item), reverse(item))
