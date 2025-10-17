# apps/dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.models import Group

# IMPORTA TUS MODELOS
from .models import Normativa, Emision, Iniciativa, Reporte, Alerta, Simulacion


# ============================================================
# HOME PUBLICO (CIUDADANO) - PORTADA SIN METRICAS INTERNAS
# ============================================================
def home_ciudadano(request):
    """
    HOME PUBLICO. MUESTRA NOTICIAS, LOGROS DESTACADOS E
    HIPERVINCULOS A REPORTES PUBLICOS. EVITA EXPONER
    METRICAS INTERNAS O DETALLES SENSIBLES.
    """

    # NOTICIAS: SI EXISTE GRUPO "CIUDADANO" Y ALERTAS CON VISIBILIDAD, USARLO
    try:
        grp = Group.objects.get(name__iexact="Ciudadano")
        alertas = Alerta.objects.filter(Q(visible_para=grp) | Q(visible_para__isnull=True)).order_by("-fecha")[:6]
    except Group.DoesNotExist:
        alertas = Alerta.objects.all().order_by("-fecha")[:6]

    noticias = []
    for a in alertas:
        # CAMPOS DEFENSIVOS
        titulo = getattr(a, "tipo", "Actualizacion")
        fecha = getattr(a, "fecha", None)
        resumen_raw = getattr(a, "mensaje", "") or ""
        resumen = resumen_raw if len(resumen_raw) <= 180 else (resumen_raw[:180] + "…")
        categoria = f"Severidad {getattr(a, 'severidad', 'NA')}"
        noticias.append({
            "titulo": titulo,
            "fecha": fecha.date() if fecha else None,
            "resumen": resumen,
            "categoria": categoria,
            "url": "#",
        })

    # LOGROS DESTACADOS: INICIATIVAS CON MAYOR AVANCE
    iniciativas_qs = Iniciativa.objects.all().order_by("-avance", "-fecha_inicio")[:6]
    logros = []
    for i in iniciativas_qs:
        logros.append({
            "nombre": getattr(i, "nombre", "Iniciativa"),
            "categoria": getattr(i, "categoria", ""),
            "ubicacion": getattr(i, "ubicacion", ""),
            "avance": getattr(i, "avance", 0),
            "reduccion_esperada": getattr(i, "reduccion_esperada", 0.0),
            "imagen": getattr(i, "imagen", None),
            "descripcion": (getattr(i, "descripcion", "") or "")[:160] + ("…" if (getattr(i, "descripcion", "") and len(getattr(i, "descripcion", "")) > 160) else ""),
        })

    # REPORTES PUBLICOS: SI TU MODELO TIENE CAMPO "publico", FILTRAR; SI NO, TOMAR ULTIMOS
    reportes_qs = Reporte.objects.all().order_by("-fecha_generacion")
    if hasattr(Reporte, "publico"):
        reportes_qs = reportes_qs.filter(publico=True)
    reportes_publicos = reportes_qs[:6]

    # NORMATIVAS PUBLICAS (BUSQUEDA LIVIANA)
    q = (request.GET.get("q") or "").strip()
    normativas = Normativa.objects.all().order_by("pais", "tipo", "nombre")[:50]
    iniciativas = Iniciativa.objects.all().order_by("-fecha_inicio")[:50]
    if q:
        normativas = normativas.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(pais__icontains=q) | Q(tipo__icontains=q)
        )[:50]
        iniciativas = iniciativas.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(categoria__icontains=q) | Q(ubicacion__icontains=q)
        )[:50]

    context = {
        # BLOQUES PUBLICOS
        "noticias": noticias,
        "logros": logros,
        "reportes_publicos": reportes_publicos,

        # BUSQUEDA PUBLICA SIMPLE (OPCIONAL)
        "normativas": normativas,
        "iniciativas": iniciativas,

        # PLACEHOLDERS OPCIONALES (POR SI TU TEMPLATE LOS USA)
        "ultima_actualizacion": None,
        "iniciativas_activas": iniciativas_qs.count(),
    }
    # IMPORTANTE: LA PLANTILLA QUE QUIERES USAR COMO HOME PUBLICO
    # PON AQUI TU NUEVA PORTADA: "dashboard/home.html"
    return render(request, "dashboard/home_ciudadano.html", context)


# ============================================================
# DASHBOARDS INTERNOS (PROTEGIDOS)
# ============================================================

@login_required
def home_director(request):
    return render(request, "dashboard/director.html")


@login_required
def home_analista(request):
    # SI QUIERES, DEJA SOLO RESUMENES/CONTADORES SIN DETALLE SENSIBLE
    normativas_total = Normativa.objects.count()
    emisiones_total = Emision.objects.count()
    iniciativas_total = Iniciativa.objects.count()
    reportes_total = Reporte.objects.count()
    alertas_total = Alerta.objects.filter(resuelta=False).count()

    context = {
        "normativas_total": normativas_total,
        "emisiones_total": emisiones_total,
        "iniciativas_total": iniciativas_total,
        "reportes_total": reportes_total,
        "alertas_total": alertas_total,
        # TABLAS RECORTADAS (OPCIONAL)
        "normativas": Normativa.objects.all().order_by("-fecha_revision")[:10],
        "emisiones": Emision.objects.all().order_by("-fecha")[:15],
        "iniciativas": Iniciativa.objects.all().order_by("-fecha_inicio")[:10],
        "reportes": Reporte.objects.all().order_by("-fecha_generacion")[:10],
        "alertas": Alerta.objects.filter(resuelta=False).order_by("-fecha")[:10],
    }
    return render(request, "dashboard/analista.html", context)


@login_required
def home_operador(request):
    return render(request, "dashboard/operador.html")


# ============================================================
# NOTAS DE ENRUTAMIENTO (AGREGA ESTO EN urls.py)
# ============================================================
# from django.urls import path
# from . import views
#
# urlpatterns = [
#     # HOME PUBLICO EN /dashboard/ (O EN LA RAIZ / SI LO INCLUYES EN urls.py PRINCIPAL)
#     path("", views.home_ciudadano, name="home_ciudadano"),
#
#     # PANELES INTERNOS
#     path("director/", views.home_director, name="home_director"),
#     path("analista/", views.home_analista, name="home_analista"),
#     path("operador/", views.home_operador, name="home_operador"),
# ]
#
# EN urls.py RAIZ PUEDES HACER:
# path("", include("apps.dashboard.urls"))           -> HOME PUBLICO EN /
# path("dashboard/", include("apps.dashboard.urls")) -> HOME PUBLICO EN /dashboard/
#
# EN settings.py:
# LOGIN_URL = "/accounts/login/"
# LOGIN_REDIRECT_URL = "/dashboard/"
# LOGOUT_REDIRECT_URL = "/dashboard/"
