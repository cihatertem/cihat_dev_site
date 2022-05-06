from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class BaseSiteMap(Sitemap):
    __slot__ = "changefreq", "priority"
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return [
            "base:home",
        ]

    def location(self, item):
        return reverse(item)
