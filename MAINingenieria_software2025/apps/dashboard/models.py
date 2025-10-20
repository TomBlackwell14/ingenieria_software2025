from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def upload_to_normativas(instance, filename):
    return f"normativas/{instance.pais}/{filename}"

def upload_to_consumos(instance, filename):
    return f"cargas_consumo/{instance.subido_por.username}/{filename}"

def upload_to_emisiones(instance, filename):
    return f"comprobantes/{instance.creado_por.username}/{filename}"

def upload_to_iniciativas(instance, filename):
    return f"iniciativas/{instance.creado_por.username}/{filename}"

def upload_to_reportes(instance, filename):
    return f"reportes/{instance.generado_por.username}/{filename}"


# ============================================================
# 1️⃣ NORMATIVAS AMBIENTALES
# ============================================================

class Normativa(models.Model):
    PAIS_CHOICES = [
        ("Chile", "Chile"),
        ("Argentina", "Argentina"),
        ("Perú", "Perú"),
        ("Brasil", "Brasil"),
        ("Colombia", "Colombia"),
        ("Uruguay", "Uruguay"),
    ]
    TIPO_CHOICES = [
        ("Emisiones", "Emisiones"),
        ("Energía", "Energía"),
        ("Residuos", "Residuos"),
        ("Transporte", "Transporte"),
        ("Otro", "Otro"),
    ]

    nombre = models.CharField(max_length=200)
    pais = models.CharField(max_length=30, choices=PAIS_CHOICES)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    estado = models.BooleanField(default=True)  # True = cumple
    fecha_revision = models.DateField(default=timezone.now)
    documento = models.FileField(upload_to=upload_to_normativas, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.pais})"


# ============================================================
# 2️⃣ INVENTARIO DE EMISIONES GEI
# ============================================================

class Emision(models.Model):
    ALCANCE_CHOICES = [
        ("1", "Alcance 1 - Directas"),
        ("2", "Alcance 2 - Indirectas (energía)"),
        ("3", "Alcance 3 - Otras indirectas"),
    ]

    fecha = models.DateField(default=timezone.now)
    unidad_negocio = models.CharField(max_length=100)
    fuente = models.CharField(max_length=100)
    alcance = models.CharField(max_length=1, choices=ALCANCE_CHOICES)
    consumo = models.FloatField(help_text="Cantidad consumida")
    unidad = models.CharField(max_length=20, default="kWh")
    factor_emision = models.FloatField(help_text="Factor en tCO₂e / unidad")
    emisiones = models.FloatField(help_text="Resultado tCO₂e", blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comprobante = models.FileField(upload_to=upload_to_emisiones, blank=True, null=True)

    def calcular_emisiones(self):
        if self.consumo and self.factor_emision:
            self.emisiones = self.consumo * self.factor_emision

    def save(self, *args, **kwargs):
        self.calcular_emisiones()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unidad_negocio} - {self.fuente} ({self.fecha.year})"


# ============================================================
# 3️⃣ CARGAS DE CONSUMO (manual o masiva)
# ============================================================

class CargaConsumo(models.Model):
    TIPO_CHOICES = [
        ("Manual", "Manual"),
        ("Masiva", "Masiva"),
    ]

    tipo_carga = models.CharField(max_length=20, choices=TIPO_CHOICES)
    archivo = models.FileField(upload_to=upload_to_consumos)
    validado = models.BooleanField(default=False)
    fecha_subida = models.DateTimeField(default=timezone.now)
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Carga {self.tipo_carga} - {self.subido_por}"


# ============================================================
# 4️⃣ SIMULACIONES (energética o normativa)
# ============================================================

class Simulacion(models.Model):
    TIPO_CHOICES = [
        ("Energetica", "Transición Energética"),
        ("Normativa", "Normativas Legales"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    parametros = models.JSONField(default=dict)
    resultado = models.JSONField(default=dict, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.tipo} ({self.fecha.strftime('%Y-%m-%d')})"


# ============================================================
# 5️⃣ INICIATIVAS DE MITIGACIÓN
# ============================================================

class Iniciativa(models.Model):
    CATEGORIA_CHOICES = [
        ("Energía", "Energía"),
        ("Transporte", "Transporte"),
        ("Residuos", "Residuos"),
        ("Otro", "Otro"),
    ]

    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    ubicacion = models.CharField(max_length=100, blank=True)
    fecha_inicio = models.DateField(default=timezone.now)
    capex = models.FloatField(help_text="Costo inicial USD", blank=True, null=True)
    opex = models.FloatField(help_text="Costo anual USD", blank=True, null=True)
    reduccion_esperada = models.FloatField(help_text="tCO₂e evitadas", blank=True, null=True)
    avance = models.FloatField(help_text="Porcentaje completado", default=0)
    descripcion = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    documento = models.FileField(upload_to=upload_to_iniciativas, blank=True, null=True)

    def costo_efectividad(self):
        if self.capex and self.reduccion_esperada:
            return round(self.capex / self.reduccion_esperada, 2)
        return None

    def __str__(self):
        return self.nombre


# ============================================================
# 6️⃣ REPORTES Y EXPORTACIONES
# ============================================================

class Reporte(models.Model):
    TIPO_CHOICES = [
        ("PDF", "PDF"),
        ("Excel", "Excel"),
        ("CSV", "CSV"),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    ruta_archivo = models.CharField(max_length=255)
    generado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_generacion = models.DateTimeField(default=timezone.now)
    archivo = models.FileField(upload_to=upload_to_reportes, blank=True, null=True)

    def __str__(self):
        return f"Reporte {self.tipo} ({self.fecha_generacion.strftime('%Y-%m-%d')})"


# ============================================================
# 7️⃣ ALERTAS / NOTIFICACIONES
# ============================================================

class Alerta(models.Model):
    TIPO_CHOICES = [
        ("Incumplimiento", "Incumplimiento normativo"),
        ("Desviación", "Desviación de meta"),
        ("Error", "Error de carga o validación"),
    ]
    SEVERIDAD_CHOICES = [
        ("Baja", "Baja"),
        ("Media", "Media"),
        ("Alta", "Alta"),
    ]

    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    severidad = models.CharField(max_length=10, choices=SEVERIDAD_CHOICES, default="Media")
    fecha = models.DateTimeField(default=timezone.now)
    visible_para = models.ManyToManyField("auth.Group", blank=True)
    resuelta = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.severidad}] {self.tipo}"


# ============================================================
# 8️⃣ PERFIL DE USUARIO (extiende User para info adicional)
# ============================================================

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    unidad_negocio = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=50, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to="perfiles/", blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"
