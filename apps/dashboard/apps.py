# apps/dashboard/apps.py
from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboard"   # RUTA DEL PAQUETE
    label = "dashboard"       # ETIQUETA UNICA
    verbose_name = "Paneles y Dashboards"
