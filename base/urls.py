from django.urls import path, include
from .views import home_page
from base.sitemaps import BaseSiteMap
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

app_name = 'base'
sitemaps = {
    "pages": BaseSiteMap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('', home_page, name='home'),
    path("api/", include("api.urls", namespace="api")),
]
