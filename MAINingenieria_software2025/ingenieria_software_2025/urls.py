from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from apps.dashboard import views as dash
from apps.accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # HOME PUBLICO (CIUDADANO)
    path("", dash.home_ciudadano, name="home"),

    # PORTAL DE ROLES
    path("roles/", accounts_views.role_gate, name="role_login"),

    # DASHBOARD PRINCIPAL (INCLUYE TODAS LAS RUTAS DE LA APP)
    path("dashboard/", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")),

    # LOGIN / LOGOUT (USANDO TEMPLATES DE REGISTRATION)
    path("accounts/login/",  auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
]

# ARCHIVOS ESTATICOS Y MEDIA EN MODO DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
