# apps/dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Avg, F, FloatField, ExpressionWrapper
from django.db.models.functions import ExtractYear
from django.contrib.auth.models import Group
from .models import Normativa, Emision, Iniciativa, Reporte, Alerta, Simulacion

# ============================================================
# DASHBOARDS INTERNOS (según rol)
# ============================================================

@login_required
def home_director(request):
    return render(request, "dashboard/director.html")

@login_required
def home_operador(request):
    return render(request, "dashboard/operador.html")

# apps/dashboard/views.py (REEMPLAZA AMBAS DEFINICIONES POR ESTA UNICA)
def home_ciudadano(request):
    from django.db.models import Q

    # SERIE HISTORICA (tCO2e = consumo * factor)
    emisions_qs = Emision.objects.annotate(
        tco2e=ExpressionWrapper(F('consumo') * F('factor_emision'), output_field=FloatField()),
        anio=ExtractYear('fecha'),
    )
    serie = (emisions_qs.values('anio').order_by('anio').annotate(total=Sum('tco2e')))
    series_historico_labels = [str(x['anio']) for x in serie]
    series_historico_emisiones = [round((x['total'] or 0.0), 1) for x in serie]

    # KPIS
    kpi_emisiones_tco2e = series_historico_emisiones[-1] if series_historico_emisiones else 0.0
    reduccion_pct = 0.0
    if len(series_historico_emisiones) >= 2 and series_historico_emisiones[0] > 0:
        base = series_historico_emisiones[0]
        reduccion_pct = round((base - kpi_emisiones_tco2e) * 100.0 / base, 1)
    cumplimiento_meta_pct = round(Iniciativa.objects.aggregate(avg=Avg('avance'))['avg'] or 0.0, 1)

    # Emisiones por fuente (ultimo anio)
    emisiones_por_fuente = []
    if series_historico_labels:
        anio_max = int(series_historico_labels[-1])
        emisiones_por_fuente = list(
            emisions_qs.filter(anio=anio_max)
            .values('fuente')
            .annotate(tco2e=Sum('tco2e'))
            .order_by('-tco2e')
        )
    fuentes_labels = [e['fuente'] for e in emisiones_por_fuente] or ['Energia','Transporte','Residuos']
    fuentes_values = [round(float(e['tco2e']), 1) for e in emisiones_por_fuente] or [60, 30, 10]

    # Noticias desde Alertas (si no tienes el campo visible_para, esto igual funciona)
    try:
        grp = Group.objects.get(name__iexact="Ciudadano")
        alertas = Alerta.objects.filter(visible_para=grp).order_by('-fecha')[:8]
    except Group.DoesNotExist:
        alertas = Alerta.objects.all().order_by('-fecha')[:8]

    noticias = []
    for a in alertas:
        resumen = a.mensaje if len(a.mensaje) <= 180 else a.mensaje[:180] + "…"
        noticias.append({
            "titulo": a.tipo,
            "categoria": f"Severidad {getattr(a, 'severidad', 'NA')}",
            "fecha": getattr(a, 'fecha', None).date() if getattr(a, 'fecha', None) else None,
            "resumen": resumen,
            "url": "#",
        })

    # Busqueda publica simple
    q = request.GET.get('q', '').strip()
    normativas = Normativa.objects.all().order_by('pais', 'tipo', 'nombre')
    iniciativas = Iniciativa.objects.all().order_by('-avance', '-fecha_inicio')
    if q:
        normativas = normativas.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(pais__icontains=q) | Q(tipo__icontains=q)
        )
        iniciativas = iniciativas.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(categoria__icontains=q) | Q(ubicacion__icontains=q)
        )

    # Reportes publicos (EVITAR .url SIN ARCHIVO EN TEMPLATE)
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
    return render(request, "dashboard/ciudadano.html", context)


@login_required
def home_analista(request):
    # Totales para KPIs
    normativas_total = Normativa.objects.count()
    emisiones_total = Emision.objects.count()
    iniciativas_total = Iniciativa.objects.count()
    reportes_total = Reporte.objects.count()
    alertas_total = Alerta.objects.filter(resuelta=False).count()

    # Listas para tablas
    normativas = Normativa.objects.all().order_by('-fecha_revision')[:10]
    emisiones = Emision.objects.all().order_by('-fecha')[:15]
    iniciativas = Iniciativa.objects.all().order_by('-fecha_inicio')[:10]
    reportes = Reporte.objects.all().order_by('-fecha_generacion')[:10]
    alertas = Alerta.objects.filter(resuelta=False).order_by('-fecha')[:10]

    context = {
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
    return render(request, "dashboard/analista.html", context)


