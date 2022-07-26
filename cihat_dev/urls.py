from django.contrib import admin
from django.urls import path, include
# static&media urls
from django.conf import settings
from django.conf.urls.static import static
#  dotenv
import os
from dotenv import load_dotenv
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

load_dotenv()

urlpatterns = [
    path(os.getenv("ADMIN_ADDRESS"), admin.site.urls),
    path('', include('base.urls', namespace='base')),
    path('api/', include('api.urls', namespace='api')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
