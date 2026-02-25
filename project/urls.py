from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from cbo.views.error import Error404View
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

handler404 = Error404View.as_view()

urlpatterns = [
    path('', include('cbo.urls')),
    path('api/', include('cbo.api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Servir arquivos estáticos e media em desenvolvimento ou quando USE_S3=FALSE
if settings.DEBUG or not settings.USE_S3:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
