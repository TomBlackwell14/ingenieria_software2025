# ================================
# APLICACIONES
# ================================
INSTALLED_APPS = [
    # DJANGO CORE
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # TUS APPS (USAR SIEMPRE AppConfig)
    "apps.accounts.apps.AccountsConfig",
    "apps.dashboard.apps.DashboardConfig",
    # DEJA ESTA LINEA SOLO SI main ES UNA APP REAL CON apps.py
    # "main.apps.MainConfig",
]

# ================================
# ENRUTADOR RAIZ
# ================================
ROOT_URLCONF = "urls"

# ================================
# WSGI / ASGI
# ================================
WSGI_APPLICATION = "wsgi.application"
