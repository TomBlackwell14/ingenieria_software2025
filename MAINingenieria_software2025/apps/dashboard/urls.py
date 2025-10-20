from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    # === DASHBOARDS POR ROL ===
    path("analista/",  views.home_analista,  name="home_analista"),
    path("director/",  views.home_director,  name="home_director"),
    path("operador/",  views.home_operador,  name="home_operador"),
    path("ciudadano/", views.home_ciudadano, name="home_ciudadano"),

    # === OPERADOR ===
    path("operador/carga-masiva/", views.post_carga_masiva, name="post_carga_masiva"),

    # === ANALISTA (TODAS LAS HU RELACIONADAS) ===
    path("analista/registro-manual/",         views.analista_registro_manual,       name="analista_registro_manual"),
    path("analista/importar-excel/",          views.analista_importar_excel,        name="analista_importar_excel"),
    path("analista/plantilla/<str:formato>/", views.analista_descargar_plantilla,   name="analista_descargar_plantilla"),
    path("analista/inventario/",              views.analista_inventario,            name="analista_inventario"),
    path("analista/exportar/<str:formato>/",  views.analista_exportar,              name="analista_exportar"),
    path("analista/bitacora/",                views.analista_bitacora,              name="analista_bitacora"),
    path("analista/simulacion/",              views.analista_simulacion,            name="analista_simulacion"),
    path("analista/simulacion/historial/",    views.analista_simulacion_historial,  name="analista_simulacion_historial"),
]
