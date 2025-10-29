"""
DJANGO SETTINGS PARA ingenieria_software_2025
"""

from pathlib import Path
import os

# ================================
# RUTAS BASE
# ================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ================================
# CLAVE SECRETA Y DEBUG
# - EN PRODUCCION USA VARIABLE DE ENTORNO
# ================================
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "DEV-INSECURE-REEMPLAZAR"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# HOSTS PERMITIDOS
# - AGREGA DOMINIOS O IPs CUANDO PUBLIQUES
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# settings.py
from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    "django.contrib.admin","django.contrib.auth","django.contrib.contenttypes",
    "django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles",
    "apps.accounts",                 # <-- IMPORTANTE
    "apps.dashboard",                # <-- IMPORTANTE
    "apps"
]

# ================================
# MIDDLEWARE
# ================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ================================
# ENRUTADOR RAIZ
# - PARA AGREGAR NUEVOS MODULOS USA EL ARCHIVO urls.py DEL PROYECTO
# ================================
ROOT_URLCONF = "ingenieria_software_2025.urls"

# === TEMPLATES ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",                                    # p.ej. .../ingenieria_software2025/templates
            BASE_DIR.parent / "MAINingenieria_software2025" / "templates",  # TU CARPETA ACTUAL
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ================================
# WSGI / ASGI
# ================================
WSGI_APPLICATION = "ingenieria_software_2025.wsgi.application"
# SI USAS ASGI/CANALES, AGREGA ASGI_APPLICATION E INSTALA DEPENDENCIAS

# ================================
# BASE DE DATOS
# - POR DEFECTO SQLITE
# - EJEMPLO ENV PARA POSTGRES ABAJO
# ================================
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        # SOLO PARA POSTGRES / MYSQL
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}
# EJEMPLO POSTGRES ENV:
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=midb
# DB_USER=miusuario
# DB_PASSWORD=secreta
# DB_HOST=localhost
# DB_PORT=5432

# ================================
# VALIDADORES DE PASSWORD
# ================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ================================
# INTERNACIONALIZACION
# ================================
LANGUAGE_CODE = "es-cl"           # LENGUAJE CHILE
TIME_ZONE = "America/Santiago"    # ZONA HORARIA CHILE
USE_I18N = True
USE_TZ = True

# ================================
# ARCHIVOS ESTATICOS Y MEDIA
# ================================
STATIC_URL = '/static/'

# Carpeta de estáticos durante el desarrollo
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Carpeta: ingenieria_software2025/static/
]

# Carpeta destino para collectstatic en producción
STATIC_ROOT = BASE_DIR / "staticfiles"

# Archivos subidos por el usuario
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ================================
# AUTENTICACION
# - REDIRECCIONES DESPUES DE LOGIN/LOGOUT
# ================================
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ================================
# DEFAULT PK
# ================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
