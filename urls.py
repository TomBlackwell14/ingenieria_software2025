from django.contrib import admin
from django.urls import path, include  # 'include' es clave
from django.conf import settings
from django.conf.urls.static import static
# from . import views  <-- ¡ELIMINA ESTA LÍNEA!

urlpatterns = [
    # HOME PUBLICO (raíz)
    # path("", views.home_ciudadano, name="home_ciudadano"), <-- ELIMINA ESTAS LÍNEAS
    # path("director/", views.home_director, name="home_director"),

    # Solución: Usa 'include()' para delegar todas las URLs de la aplicación 'main'
    path("", include('main.urls')),
    
    path("admin/", admin.site.urls), # Siempre mantén el admin
]

# SERVIR STATIC/MEDIA EN DESARROLLO
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)