# apps/dashboard/views.py

# ============================================================
# IMPORTS GENERALES
# ============================================================
from datetime import date
import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Sum, Avg, F, FloatField, ExpressionWrapper
from django.db.models.functions import ExtractYear
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .models import Normativa, Emision, Iniciativa, Reporte, Alerta

# ============================================================
# CONSTANTES Y HELPERS
# ============================================================
ANIOS_DEFAULT = [2023, 2024, 2025]
UNIDADES_NEGOCIO_DEFAULT = [{"id": "default", "nombre": "General"}]

def _get_anios():
    """
    INTENTA DERIVAR ANIOS DESDE EMISION.FECHA; SI NO HAY DATOS, RETORNA DEFAULTS
    """
    try:
        qs = (Emision.objects
              .exclude(fecha__isnull=True)
              .annotate(anio=ExtractYear('fecha'))
              .values_list('anio', flat=True)
              .distinct().order_by('anio'))
        anios = [int(a) for a in qs if a]
        return anios or ANIOS_DEFAULT
    except Exception:
        return ANIOS_DEFAULT

def _get_unidades_negocio():
    """
    INTENTA DERIVAR UNIDADES DE NEGOCIO DESDE EMISION.UNIDAD_NEGOCIO
    DEBES AJUSTAR EL CAMPO SEGUN TU MODELO (ESTE ES UN PLACEHOLDER)
    """
    items = []
    try:
        # SI TU MODELO TIENE FK A UNIDADNEGOCIO, PUEDES HACER .values('unidad_negocio__id','unidad_negocio__nombre')
        qs = (Emision.objects
              .values('unidad_negocio')  # AJUSTA NOMBRE DE CAMPO SI ES DIFERENTE
              .annotate(cnt=Sum(F('consumo_cantidad') * 0 + 1))
              .order_by('unidad_negocio'))
        for r in qs:
            val = r.get('unidad_negocio') or "General"
            items.append({"id": val, "nombre": str(val)})
        return items or UNIDADES_NEGOCIO_DEFAULT
    except Exception:
        return UNIDADES_NEGOCIO_DEFAULT

def _contexto_base_analista(extra=None):
    """
    CONTEXTO BASE PARA home_analista.html CON VALORES SEGUROS
    """
    ctx = {
        "kpi_total": "12.480",
        "kpi_meta": "82%",
        "kpi_iniciativas": "17",
        "kpi_auditorias": "3",
        "anios": _get_anios(),
        "unidades_negocio": _get_unidades_negocio(),
        "inventario": [],
        "page_obj": None,
    }
    if extra:
        ctx.update(extra)
    return ctx

# ============================================================
# DASHBOARDS INTERNOS SEGUN ROL
# ============================================================
@login_required
def home_director(request):
    # Datos simulados
    context = {
        'kpis': {
            'fecha_actualizacion': "2025-10-24",
            'linea_base_tco2e': 150.0,
            'meta_tco2e': 100.0,
            'actual_tco2e': 95.0,
        },
        'metas': {
            'linea_base_tco2e': 150.0,
            'meta_tco2e': 100.0,
            'actual_tco2e': 95.0,
            'anio_base': 2023,
            'anio_meta': 2025,
        },
        'links': {
            'metodologia': "#",
            'descargar_pdf': "#",
            'descargar_excel': "#",
        },
        'tendencia': [
            {'anio': 2023, 'emisiones': 150.0},
            {'anio': 2024, 'emisiones': 120.0},
            {'anio': 2025, 'emisiones': 95.0},
        ],
        'top_fuentes': [
            {'fuente': 'Combustible', 'emisiones': 50.0},
            {'fuente': 'Electricidad', 'emisiones': 30.0},
            {'fuente': 'Refrigerantes', 'emisiones': 15.0},
        ],
        'alertas': [
            {'titulo': 'Desviación alta', 'descripcion': 'Las emisiones actuales superan el umbral esperado.', 'nivel': 'rojo', 'color': '#d14343'},
            {'titulo': 'Meta alcanzada', 'descripcion': 'Las emisiones actuales están dentro del rango esperado.', 'nivel': 'verde', 'color': '#2e7d32'},
        ],
    }
    return render(request, 'dashboard/home_director.html', context)

def home_operador(request):
    """
    PANEL OPERADOR: CONSTRUYE LINKS CON REVERSE SIN DEPENDER DEL NAMESPACE
    EVITAMOS request.resolver_match.namespace_list (NO EXISTE EN DJANGO 5)
    """
    def urln(name, default="#"):
        try:
            return reverse(name)
        except NoReverseMatch:
            try:
                return reverse(f"dashboard:{name}")
            except NoReverseMatch:
                return default

    context = {
        "links": {
            "inventario": urln("inventario"),
            "descargar_excel": urln("descargar_excel"),
            "descargar_pdf": urln("descargar_pdf"),
            "post_carga_manual": urln("post_carga_manual"),
            "post_ejecutar_conversion": urln("post_ejecutar_conversion"),
        },
        "kpis": {"fecha_actualizacion": None},
        "cola": {
            "archivos_pendientes": 0,
            "ultima_conversion": "—",
            "registros_error": 0,
            "validaciones": "GHG + Consistencias basicas",
        },
        "conversion": {
            "factor": "GHG 2023/24",
            "ultima_ejecucion": "—",
            "estado": "Listo",
            "estado_color": "verde",
        },
        "conversion_log": [],
        "ultimos": [],
    }
    return render(request, "dashboard/home_operador.html", context)

# ============================================================
# HOME ANALISTA (PROTEGIDO) + CONTEXTO REAL
# ============================================================
@login_required
def home_analista(request):
    """
    RENDERIZA EL PANEL DEL ANALISTA CON KPIS REALES (SI HAY DATOS) Y CONTEXTO BASE
    """
    # Datos simulados
    inventario = [
        {'anio': 2023, 'total': 120.5},
        {'anio': 2024, 'total': 110.3},
        {'anio': 2025, 'total': 95.7},
    ]

    context = {
        'kpi_total': "12.480",
        'kpi_meta': "82%",
        'kpi_iniciativas': "17",
        'kpi_auditorias': "3",
        'anios': [2023, 2024, 2025],
        'unidades_negocio': [
            {"id": "default", "nombre": "General"},
        ],
        'inventario': inventario,
        'page_obj': None,
    }
    return render(request, 'dashboard/home_analista.html', context)

# ============================================================
# PORTAL CIUDADANO (PUBLICO)
# ============================================================
def home_ciudadano(request):
    # Datos simulados
    emisions_qs = [
        {'anio': 2023, 'total': 120.5},
        {'anio': 2024, 'total': 110.3},
        {'anio': 2025, 'total': 95.7},
    ]

    series_historico_labels = [str(x['anio']) for x in emisions_qs]
    series_historico_emisiones = [round(x['total'], 1) for x in emisions_qs]

    kpi_emisiones_tco2e = series_historico_emisiones[-1] if series_historico_emisiones else 0.0
    reduccion_pct = 0.0
    if len(series_historico_emisiones) >= 2 and series_historico_emisiones[0] > 0:
        reduccion_pct = round(
            ((series_historico_emisiones[0] - series_historico_emisiones[-1]) / series_historico_emisiones[0]) * 100,
            1,
        )

    cumplimiento_meta_pct = 85.0  # Simulación

    emisiones_por_fuente = [
        {'fuente': 'Combustible', 'total': 50.0},
        {'fuente': 'Electricidad', 'total': 30.0},
        {'fuente': 'Refrigerantes', 'total': 15.0},
    ]

    context = {
        'series_historico_labels': series_historico_labels,
        'series_historico_emisiones': series_historico_emisiones,
        'kpi_emisiones_tco2e': kpi_emisiones_tco2e,
        'reduccion_pct': reduccion_pct,
        'cumplimiento_meta_pct': cumplimiento_meta_pct,
        'emisiones_por_fuente': emisiones_por_fuente,
    }
    return render(request, 'dashboard/home_ciudadano.html', context)

# ============================================================
# HANDLERS DE CARGAS (OPERADOR)
# ============================================================
@login_required
@require_POST
def post_carga_masiva(request):
    f = request.FILES.get('archivo')
    if not f:
        messages.error(request, "No se adjunto ningun archivo.")
        return redirect("home_operador")

    nombre = (getattr(f, "name", "") or "").lower()
    content_type = (getattr(f, "content_type", "") or "").lower()
    ext_ok = nombre.endswith((".xlsx", ".xls"))
    mime_ok = content_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "", "application/octet-stream",
    )
    if not ext_ok or not mime_ok:
        messages.error(request, "El archivo debe ser Excel (.xlsx o .xls).")
        return redirect("home_operador")

    # TODO: PROCESAR CON PANDAS/OPENPYXL
    messages.success(request, "Archivo recibido. (Procesamiento pendiente)")
    return redirect("home_operador")

# ============================================================
# ENDPOINTS ANALISTA (HU-02/HU-06/HU-07/HU-03/HU-04 + SIMULACION)
# ============================================================
@login_required
@require_http_methods(["POST"])
def analista_registro_manual(request):
    """
    HU-02/HU-07: RECIBE EL FORM DE CARGA MANUAL. VALIDACION BASICA Y REDIRECCION.
    LUEGO CALCULA TCO2E EN SERVIDOR Y PERSISTE EN BD (PENDIENTE).
    """
    tipo_consumo = request.POST.get("tipo_consumo")
    unidad = request.POST.get("unidad")
    cantidad = request.POST.get("cantidad")
    fecha = request.POST.get("fecha")

    if not (tipo_consumo and unidad and cantidad and fecha):
        ctx = _contexto_base_analista({"form_error": "FALTAN CAMPOS OBLIGATORIOS EN CARGA MANUAL"})
        return render(request, "dashboard/home_analista.html", ctx)

    # TODO: CALCULAR TCO2E CON TABLAS OFICIALES Y GUARDAR EN BD
    messages.success(request, "Registro manual recibido. (Calculo oficial pendiente)")
    return redirect("home_analista")

@login_required
@require_http_methods(["POST"])
def analista_importar_excel(request):
    """
    HU-06: IMPORTA EXCEL. POR AHORA SOLO CONFIRMA RECEPCION.
    """
    f = request.FILES.get("archivo")
    if not f:
        ctx = _contexto_base_analista({"form_error": "NO SE ADJUNTO ARCHIVO"})
        return render(request, "dashboard/home_analista.html", ctx)

    # TODO: PROCESAR EXCEL Y GUARDAR REGISTROS
    ctx = _contexto_base_analista({"import_ok": f"CARGA MASIVA RECIBIDA: {f.name}"})
    return render(request, "dashboard/home_analista.html", ctx)

@login_required
def analista_descargar_plantilla(request, formato="csv"):
    """
    ENTREGA UNA PLANTILLA MINIMA PARA CARGA MASIVA (CSV)
    """
    header = ["fecha","tipo_consumo","unidad","cantidad","pais","unidad_negocio","detalle"]
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(header)
    writer.writerow([date.today().isoformat(),"electricidad","kwh","1000","CL","General","ALUMBRADO"])
    content = csv_buffer.getvalue()
    resp = HttpResponse(content, content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="plantilla_inventario.csv"'
    return resp

@login_required
def analista_inventario(request):
    """
    HU-03: APLICA FILTROS Y RENDERIZA INVENTARIO. POR AHORA SIN BD DEVUELVE VACIO.
    CUANDO CONECTES BD, ARMA LA QUERY Y PAGINACION AHI.
    """
    ctx = _contexto_base_analista()
    return render(request, "dashboard/home_analista.html", ctx)

@login_required
def analista_exportar(request, formato="csv"):
    """
    HU-04: EXPORTA INVENTARIO SEGUN FILTROS ACTIVOS. POR AHORA DEVUELVE CSV VACIO.
    """
    header = ["fecha","alcance","fuente","unidad","cantidad","tco2e","pais","unidad_negocio"]
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(header)
    content = csv_buffer.getvalue()
    resp = HttpResponse(content, content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="inventario_export.csv"'
    return resp

@login_required
def analista_bitacora(request):
    """
    HU-04: BITACORA SIMPLE MOCK
    """
    data = [
        {"evento":"CREACION","detalle":"REGISTRO MANUAL","usuario":"analista","ts":timezone.now().isoformat()},
    ]
    return JsonResponse({"bitacora": data})

@login_required
@require_http_methods(["POST"])
def analista_simulacion(request):
    """
    SIMULACION DE POLITICAS PUBLICAS (ESCENARIOS) MOCK
    """
    try:
        anio_base = int(request.POST.get("anio_base", "2025"))
    except ValueError:
        anio_base = 2025
    tipo = request.POST.get("tipo_politica")
    try:
        valor = float(request.POST.get("valor_politica", "0") or 0)
    except ValueError:
        valor = 0.0
    ambito = request.POST.get("ambito", "total")

    base = 12480.0
    sim = base

    if tipo == "limite":
        sim = min(base, valor)
    elif tipo == "impuesto":
        # IMPUESTO CALCULA COSTO, NO MODIFICA TCO2E
        pass
    elif tipo == "meta_reduccion":
        sim = base * max(0.0, (1.0 - valor/100.0))

    delta = sim - base
    costo = valor * sim if tipo == "impuesto" else None

    simulacion = {
        "base_tco2e": round(base, 3),
        "sim_tco2e": round(sim, 3),
        "delta_tco2e": round(delta, 3),
        "costo_est": round(costo, 2) if costo is not None else None,
        "anio_base": anio_base,
        "tipo": tipo,
        "ambito": ambito,
    }

    ctx = _contexto_base_analista({"simulacion": simulacion})
    return render(request, "dashboard/home_analista.html", ctx)

@login_required
def analista_simulacion_historial(request):
    """
    LISTA DE ESCENARIOS DE SIMULACION (MOCK)
    """
    data = [
        {"anio_base": 2025, "tipo": "meta_reduccion", "valor": 10, "resultado_tco2e": 11232.0},
    ]
    return JsonResponse({"escenarios": data})

@login_required
def home_gerente(request):
    # Datos simulados para el gerente
    context = {
        'kpis': {
            'fecha_actualizacion': "2025-10-24",
            'linea_base_tco2e': 200.0,
            'meta_tco2e': 120.0,
            'actual_tco2e': 110.0,
        },
        'metas': {
            'linea_base_tco2e': 200.0,
            'meta_tco2e': 120.0,
            'actual_tco2e': 110.0,
            'anio_base': 2020,
            'anio_meta': 2025,
        },
        'links': {
            'metodologia': "#",
            'descargar_pdf': "#",
            'descargar_excel': "#",
        },
        'tendencia': [
            {'anio': 2020, 'emisiones': 200.0},
            {'anio': 2021, 'emisiones': 180.0},
            {'anio': 2022, 'emisiones': 150.0},
            {'anio': 2023, 'emisiones': 130.0},
            {'anio': 2024, 'emisiones': 120.0},
            {'anio': 2025, 'emisiones': 110.0},
        ],
        'top_fuentes': [
            {'fuente': 'Transporte', 'emisiones': 80.0},
            {'fuente': 'Industria', 'emisiones': 50.0},
            {'fuente': 'Oficinas', 'emisiones': 30.0},
        ],
        'alertas': [
            {'titulo': 'Incremento en transporte', 'descripcion': 'Las emisiones por transporte han aumentado.', 'nivel': 'amarillo', 'color': '#fbc02d'},
            {'titulo': 'Meta alcanzada', 'descripcion': 'Las emisiones actuales están dentro del rango esperado.', 'nivel': 'verde', 'color': '#2e7d32'},
        ],
    }
    return render(request, "dashboard/home_gerente.html", context)

@login_required
def home_coordinador(request):
    # Datos simulados para el coordinador
    context = {
        'kpis': {
            'fecha_actualizacion': "2025-10-24",
        },
        'iniciativas': [
            {'nombre': 'Eficiencia Energética', 'descripcion': 'Reducción del consumo en oficinas.', 'ubicacion': 'Santiago', 'fecha': '2025-01-15', 'categoria': 'Energía'},
            {'nombre': 'Transporte Verde', 'descripcion': 'Uso de vehículos eléctricos.', 'ubicacion': 'Valparaíso', 'fecha': '2025-03-10', 'categoria': 'Transporte'},
        ],
    }
    return render(request, "dashboard/home_coordinador.html", context)

# apps/dashboard/views.py

from django.shortcuts import redirect
from django.urls import reverse
from datetime import date

def analista_registro_manual(request):
    if request.method == "POST":
        # TODO: VALIDAR Y GUARDAR (VER PASO 2 PARA tCO2e)
        # REDIRIGIR AL INVENTARIO PARA RECONSTRUIR SERIES Y VER EL GRAFICO
        url = reverse("dashboard:analista_inventario")
        return redirect(f"{url}#inventario")

    # GET: RENDER DEL FORM (SI APLICA)
    # return render(request, "dashboard/analista.html", {...})
