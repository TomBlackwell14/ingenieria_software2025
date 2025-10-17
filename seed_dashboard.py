"""
Carga inicial de datos de ejemplo para el panel Analista Ambiental
Ejecutar con:
    python manage.py shell < seed_dashboard.py
"""

import random
from datetime import date, timedelta
from django.contrib.auth.models import User
from apps.dashboard.models import (
    Normativa, Emision, Iniciativa, CargaConsumo,
    Simulacion, Reporte, Alerta
)

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def rand_date(years=3):
    """Genera una fecha aleatoria en los últimos N años"""
    start = date.today() - timedelta(days=365 * years)
    end = date.today()
    return start + timedelta(days=random.randint(0, (end - start).days))

# ============================================================
# CREAR USUARIO BASE
# ============================================================

analista, _ = User.objects.get_or_create(username="analista_demo", defaults={"password": "analista123"})

# ============================================================
# 1️⃣ NORMATIVAS AMBIENTALES
# ============================================================

paises = ["Chile", "Argentina", "Perú", "Brasil", "Colombia", "Uruguay", "México", "Ecuador", "Bolivia"]
tipos = ["Emisiones", "Energía", "Residuos", "Transporte"]

normativas = [
    ("Ley de Eficiencia Energética", "Energía"),
    ("Protocolo de Gestión de Residuos Industriales", "Residuos"),
    ("Reglamento de Emisiones Vehiculares", "Transporte"),
    ("Decreto de Huella de Carbono", "Emisiones"),
    ("Norma ISO 14001 Adaptada", "Emisiones"),
    ("Ley de Reciclaje Urbano", "Residuos"),
    ("Plan Nacional de Energía Limpia", "Energía"),
]

for pais in paises:
    for nombre, tipo in random.sample(normativas, k=4):
        Normativa.objects.get_or_create(
            nombre=f"{nombre} - {pais}",
            pais=pais,
            tipo=tipo,
            estado=random.choice([True, True, True, False]),
            descripcion=f"Marco regulatorio de {tipo.lower()} en {pais}.",
        )

print(f"✅ Creadas {Normativa.objects.count()} normativas.")

# ============================================================
# 2️⃣ EMISIONES GEI
# ============================================================

fuentes = ["Electricidad", "Combustible", "Gas Natural", "Refrigerantes"]
alcances = ["1", "2", "3"]
unidades = ["kWh", "L", "m³"]

for _ in range(60):
    Emision.objects.create(
        fecha=rand_date(4),
        unidad_negocio=random.choice(["Retail CL", "Logística AR", "Centro Perú", "Oficina BR"]),
        fuente=random.choice(fuentes),
        alcance=random.choice(alcances),
        consumo=round(random.uniform(500, 20000), 2),
        unidad=random.choice(unidades),
        factor_emision=round(random.uniform(0.0002, 0.0006), 6),
        creado_por=analista,
    )

print(f"✅ Creadas {Emision.objects.count()} emisiones.")

# ============================================================
# 3️⃣ CARGAS DE CONSUMO
# ============================================================

for tipo in ["Manual", "Masiva"]:
    for _ in range(3):
        CargaConsumo.objects.create(
            tipo_carga=tipo,
            archivo="cargas_consumo/demo.xlsx",
            validado=random.choice([True, False]),
            subido_por=analista,
        )

print(f"✅ Creadas {CargaConsumo.objects.count()} cargas de consumo.")

# ============================================================
# 4️⃣ INICIATIVAS DE MITIGACIÓN
# ============================================================

iniciativas = [
    ("Paneles Solares en Tiendas", "Energía"),
    ("Optimización de Transporte Logístico", "Transporte"),
    ("Programa de Compostaje", "Residuos"),
    ("Reemplazo de Calefacción Diesel", "Energía"),
    ("Eficiencia Energética en Centros", "Energía"),
]

for nombre, categoria in iniciativas:
    Iniciativa.objects.create(
        nombre=nombre,
        categoria=categoria,
        ubicacion=random.choice(paises),
        fecha_inicio=rand_date(3),
        capex=round(random.uniform(10000, 200000), 2),
        opex=round(random.uniform(1000, 10000), 2),
        reduccion_esperada=round(random.uniform(100, 2500), 2),
        avance=random.randint(20, 90),
        descripcion=f"Iniciativa de mitigación en el área de {categoria.lower()}",
        creado_por=analista,
    )

print(f"✅ Creadas {Iniciativa.objects.count()} iniciativas.")

# ============================================================
# 5️⃣ SIMULACIONES
# ============================================================

for tipo in ["Energetica", "Normativa"]:
    for _ in range(2):
        Simulacion.objects.create(
            tipo=tipo,
            parametros={"param1": random.randint(0, 100)},
            resultado={"cumple": random.choice([True, False])},
            creado_por=analista,
        )

print(f"✅ Creadas {Simulacion.objects.count()} simulaciones.")

# ============================================================
# 6️⃣ REPORTES
# ============================================================

for tipo in ["PDF", "Excel"]:
    for _ in range(3):
        Reporte.objects.create(
            tipo=tipo,
            ruta_archivo=f"/reportes/{tipo.lower()}_{random.randint(100,999)}.pdf",
            generado_por=analista,
        )

print(f"✅ Creados {Reporte.objects.count()} reportes.")

# ============================================================
# 7️⃣ ALERTAS
# ============================================================

tipos_alertas = ["Incumplimiento", "Desviación", "Error"]
for _ in range(8):
    Alerta.objects.create(
        tipo=random.choice(tipos_alertas),
        mensaje=random.choice([
            "Incumplimiento de norma ambiental detectado.",
            "Desviación del 5% sobre la meta anual.",
            "Error en carga masiva detectado.",
        ]),
        severidad=random.choice(["Baja", "Media", "Alta"]),
        resuelta=random.choice([False, True]),
    )

print(f"✅ Creadas {Alerta.objects.count()} alertas.")

print("\n🎉 Base de datos inicial creada exitosamente con datos de ejemplo realistas.\n")
