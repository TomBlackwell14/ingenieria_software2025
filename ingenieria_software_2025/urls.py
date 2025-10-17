# ingenieria_software_2025/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # HOME (SELECCION DE ROL)
    path("", include("apps.accounts.urls")),

    # DASHBOARDS POR ROL
    path("dashboard/", include("apps.dashboard.urls")),

    # LOGIN/LOGOUT/PASSWORD RESET DE DJANGO
    path("accounts/", include("django.contrib.auth.urls")),
]

# SERVIR STATIC/MEDIA EN DESARROLLO
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
