# apps/accounts/views.py
from django.shortcuts import render, redirect

def role_gate(request):
    # SI YA ESTA LOGUEADO Y LLEGA CON ?role=, REDIRIGE AL DASHBOARD
    role = request.GET.get("role")
    if request.user.is_authenticated and role:
        return redirect(f"/dashboard/{role}/")
    return render(request, "accounts/role_login.html")


def analista_inventario(request):
    # ...
    agg = (
        qs.annotate(anio=ExtractYear('fecha'))
          .values('anio')
          .annotate(total=Sum('tco2e'))
          .order_by('anio')
    )

    series_anios = [row['anio'] for row in agg if row['anio'] is not None]
    series_tco2e = [float(row['total'] or 0) for row in agg if row['anio'] is not None]

    context = {
        'inventario': page_obj,
        'page_obj': page_obj,
        'anios': obtener_anios_posibles(),
        'unidades_negocio': UnidadNegocio.objects.all(),
        'series_anios_json': json.dumps(series_anios),
        'series_tco2e_json': json.dumps(series_tco2e),
    }
    return render(request, 'dashboard/home_analista.html', context)
