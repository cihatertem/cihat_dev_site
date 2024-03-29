from django.contrib import admin
from django.urls import path, include
# static&media urls
from django.conf import settings
from django.conf.urls.static import static
#  dotenv
import os

urlpatterns = [
    path(os.getenv("ADMIN_ADDRESS"), admin.site.urls),
    path('', include('base.urls', namespace='base')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
