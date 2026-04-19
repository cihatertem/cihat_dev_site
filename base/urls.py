from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.generic import TemplateView

from base.sitemaps import BaseSiteMap

from .views import home_page

app_name = 'base'
sitemaps = {
    "pages": BaseSiteMap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('', home_page, name='home'),
]

