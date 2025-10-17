# apps/dashboard/urls.py
from django.urls import path
from . import views  # IMPORTA EL MODULO COMPLETO PARA EVITAR ERRORES AL RENOMBRAR

app_name = "dashboard"

urlpatterns = [
    path("", views.home_ciudadano, name="home_ciudadano"),   # <- HOME PUBLICO EN /dashboard/ y/o /
    path("director/", views.home_director, name="home_director"),
    path("analista/", views.home_analista, name="home_analista"),
    path("operador/", views.home_operador, name="home_operador"),
]
