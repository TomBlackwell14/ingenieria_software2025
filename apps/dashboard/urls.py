# apps/dashboard/urls.py
from django.urls import path
from . import views  # IMPORTA EL MODULO COMPLETO PARA EVITAR ERRORES AL RENOMBRAR

app_name = "dashboard"

urlpatterns = [
    path("analista/",  views.home_analista,  name="dash_analista"),
    path("director/",  views.home_director,  name="dash_director"),
    path("operador/",  views.home_operador,  name="home_operador"),  
    path("ciudadano/", views.home_ciudadano, name="dash_ciudadano"),
]
