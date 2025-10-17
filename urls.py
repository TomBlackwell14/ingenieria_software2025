# ingenieria_software_2025/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),      # HOME / LOGIN VISUAL
    path("dashboard/", include("apps.dashboard.urls")),  # << ESTE INCLUDE
    path("accounts/", include("django.contrib.auth.urls")),
    # ingenieria_software_2025/urls.py (raíz del proyecto)


]
