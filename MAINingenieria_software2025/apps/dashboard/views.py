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
              .annotate(cnt=Sum(F('consumo') * 0 + 1))
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
    # VISTA PROTEGIDA PARA DIRECTOR
    return render(request, "dashboard/home_director.html")

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
    # KPIS REALES SI EXISTEN, CON FALLBACK SI LA TABLA ESTA VACIA
    try:
        normativas_total = Normativa.objects.count()
        emisiones_total = Emision.objects.count()
        iniciativas_total = Iniciativa.objects.count()
        reportes_total = Reporte.objects.count()
        alertas_total = Alerta.objects.filter(resuelta=False).count()

        normativas = Normativa.objects.all().order_by('-fecha_revision')[:10]
        emisiones = Emision.objects.all().order_by('-fecha')[:15]
        iniciativas = Iniciativa.objects.all().order_by('-fecha_inicio')[:10]
        reportes = Reporte.objects.all().order_by('-fecha_generacion')[:10]
        alertas = Alerta.objects.filter(resuelta=False).order_by('-fecha')[:10]

        extra = {
            "normativas_total": normativas_total,
            "emisiones_total": emisiones_total,
            "iniciativas_total": iniciativas_total,
            "reportes_total": reportes_total,
            "alertas_total": alertas_total,
            "normativas": normativas,
            "emisiones": emisiones,
            "iniciativas": iniciativas,
            "reportes": reportes,
            "alertas": alertas,
        }
    except Exception:
        extra = {}

    return render(request, "dashboard/home_analista.html", _contexto_base_analista(extra))

# ============================================================
# PORTAL CIUDADANO (PUBLICO)
# ============================================================
def home_ciudadano(request):
    emisions_qs = Emision.objects.annotate(
        tco2e=ExpressionWrapper(F('consumo') * F('factor_emision'), output_field=FloatField()),
        anio=ExtractYear('fecha'),
    )
    serie = emisions_qs.values('anio').order_by('anio').annotate(total=Sum('tco2e'))
    series_historico_labels = [str(x['anio']) for x in serie]
    series_historico_emisiones = [round((x['total'] or 0.0), 1) for x in serie]

    kpi_emisiones_tco2e = series_historico_emisiones[-1] if series_historico_emisiones else 0.0
    reduccion_pct = 0.0
    if len(series_historico_emisiones) >= 2 and series_historico_emisiones[0] > 0:
        base = series_historico_emisiones[0]
        reduccion_pct = round((base - kpi_emisiones_tco2e) * 100.0 / base, 1)
    cumplimiento_meta_pct = round(Iniciativa.objects.aggregate(avg=Avg('avance'))['avg'] or 0.0, 1)

    emisiones_por_fuente = []
    if series_historico_labels:
        anio_max = int(series_historico_labels[-1])
        emisiones_por_fuente = list(
            emisions_qs.filter(anio=anio_max)
            .values('fuente')
            .annotate(tco2e=Sum('tco2e'))
            .order_by('-tco2e')
        )
    fuentes_labels = [e['fuente'] for e in emisiones_por_fuente] or ['Energia', 'Transporte', 'Residuos']
    fuentes_values = [round(float(e['tco2e']), 1) for e in emisiones_por_fuente] or [60, 30, 10]

    try:
        grp = Group.objects.get(name__iexact="Ciudadano")
        alertas = Alerta.objects.filter(visible_para=grp).order_by('-fecha')[:8]
    except Group.DoesNotExist:
        alertas = Alerta.objects.all().order_by('-fecha')[:8]

    noticias = []
    for a in alertas:
        msg = a.mensaje or ""
        resumen = msg if len(msg) <= 180 else msg[:180] + "…"
        noticias.append({
            "titulo": a.tipo,
            "categoria": f"Severidad {getattr(a, 'severidad', 'NA')}",
            "fecha": getattr(a, 'fecha', None).date() if getattr(a, 'fecha', None) else None,
            "resumen": resumen,
            "url": "#",
        })

    q = (request.GET.get('q') or '').strip()
    normativas = Normativa.objects.all().order_by('pais', 'tipo', 'nombre')
    iniciativas = Iniciativa.objects.all().order_by('-avance', '-fecha_inicio')
    if q:
        from django.db.models import Q
        normativas = normativas.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(pais__icontains=q) | Q(tipo__icontains=q)
        )
        iniciativas = iniciativas.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(categoria__icontains=q) | Q(ubicacion__icontains=q)
        )

    reportes_publicos = Reporte.objects.all().order_by('-fecha_generacion')[:10]

    context = {
        "kpi_emisiones_tco2e": kpi_emisiones_tco2e,
        "reduccion_pct": reduccion_pct,
        "cumplimiento_meta_pct": cumplimiento_meta_pct,
        "series_historico_labels": series_historico_labels,
        "series_historico_emisiones": series_historico_emisiones,
        "emisiones_por_fuente": emisiones_por_fuente,
        "fuentes_labels": fuentes_labels,
        "fuentes_values": fuentes_values,
        "noticias": noticias,
        "iniciativas": iniciativas,
        "reportes_publicos": reportes_publicos,
        "normativas": normativas,
        "energia_renovable_pct": 0,
        "tco2e_compensadas": 0,
        "comunidades_beneficiadas": 0,
        "arboles_plantados": 0,
    }
    return render(request, "dashboard/home_ciudadano.html", context)

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
    CUANDO CONECTES BD, ARMA LA QUERY Y PAGINACION AQUI.
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


def home_coordinador(request):
    iniciativas = Iniciativa.objects.all()
    return render(request, "dashboard/home_coordinador.html", {"iniciativas": iniciativas})


@login_required
def home_gerente(request):
    """
    Panel del gerente: entrega series históricas de emisiones para el gráfico.
    Si no hay datos en BD, se devuelven valores por defecto (simulados).
    """
    try:
        emisions_qs = Emision.objects.annotate(
            tco2e=ExpressionWrapper(F('consumo') * F('factor_emision'), output_field=FloatField()),
            anio=ExtractYear('fecha'),
        )
        serie = (emisions_qs.values('anio').order_by('anio').annotate(total=Sum('tco2e')))
        anios = [int(x['anio']) for x in serie]
        emisiones = [round((x['total'] or 0.0), 1) for x in serie]
    except Exception:
        anios = [2016,2017,2018,2019,2020,2021,2022,2023,2024]
        emisiones = [72000,70000,69000,68000,66000,64000,62000,60000,58000]

    context = {
        'anios': anios,
        'emisiones': emisiones,
    }
    return render(request, 'dashboard/home_gerente.html', context)