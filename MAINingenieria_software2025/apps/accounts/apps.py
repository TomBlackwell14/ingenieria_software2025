# apps/accounts/apps.py
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        # CREA GRUPOS AL INICIAR EL SERVIDOR (IDEMPOTENTE)
        from django.contrib.auth.models import Group
        for g in ["Director", "Operador", "Analista", "Ciudadano"]:
            Group.objects.get_or_create(name=g)
