from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import F
# NOTA: NO SE CAMBIAN CAMPOS DE BD; SOLO SE AGREGAN ALIAS EN EL MANAGER

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
# 1) NORMATIVAS AMBIENTALES
# ============================================================

class Normativa(models.Model):
    PAIS_CHOICES = [
        ("CL", "Chile"),
        ("AR", "Argentina"),
        ("PE", "Peru"),
        ("BR", "Brasil"),
        ("CO", "Colombia"),
        ("UY", "Uruguay"),
    ]
    TIPO_CHOICES = [
        ("Emisiones", "Emisiones"),
        ("Energia", "Energia"),
        ("Residuos", "Residuos"),
        ("Transporte", "Transporte"),
        ("Otro", "Otro"),
    ]

    nombre = models.CharField(max_length=200)
    pais = models.CharField(max_length=2, choices=PAIS_CHOICES)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    estado = models.BooleanField(default=True)  # TRUE = CUMPLE
    fecha_revision = models.DateField(default=timezone.now)
    documento = models.FileField(upload_to=upload_to_normativas, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_pais_display()})"


# ============================================================
# 2) INVENTARIO DE EMISIONES GEI (REGISTRO DE CONSUMO + RESULTADO)
# ============================================================

# --- QUERYSET Y MANAGER CON ALIAS ORM ---
class EmisionQuerySet(models.QuerySet):
    # AGREGA ALIAS USADOS EN CONSULTAS EXISTENTES: "consumo", "factor", "emisiones"
    def with_aliases(self):
        return self.annotate(
            consumo=F('consumo_cantidad'),
            factor=F('factor_tco2e_por_unidad'),
            emisiones=F('emisiones_tco2e'),
        )

class EmisionManager(models.Manager):
    def get_queryset(self):
        # ANOTAR SIEMPRE PARA QUE FILTER/ORDER_BY/VALUES SOBRE "consumo" FUNCIONE
        return EmisionQuerySet(self.model, using=self._db).with_aliases()


class Emision(models.Model):
    # ALCANCE SEGUN GHG
    ALCANCE_CHOICES = [
        ("1", "Alcance 1 - Directas"),
        ("2", "Alcance 2 - Indirectas (energia)"),
        ("3", "Alcance 3 - Otras indirectas"),
    ]

    # PAISES EN ISO-2 PARA CONSISTENCIA CON FRONTEND
    PAIS_CHOICES = [
        ("CL", "Chile"),
        ("AR", "Argentina"),
        ("PE", "Peru"),
        ("BR", "Brasil"),
        ("CO", "Colombia"),
        ("UY", "Uruguay"),
    ]

    # FUENTE GENERAL PARA FILTROS SIMPLES
    FUENTE_CHOICES = [
        ("combustible", "Combustible"),
        ("electricidad", "Electricidad"),
        ("refrigerantes", "Refrigerantes"),
        ("otros", "Otros"),
    ]

    # ---------- CAMPOS CLAVE ----------
    fecha = models.DateField(default=timezone.now)                      # FECHA DEL CONSUMO
    pais = models.CharField(max_length=2, choices=PAIS_CHOICES)         # PAIS (ISO-2)
    region = models.CharField(max_length=100, blank=True)               # REGION/PROV OPCIONAL
    unidad_negocio = models.CharField(max_length=120, blank=True)       # UNIDAD DE NEGOCIO OPCIONAL
    alcance = models.CharField(max_length=1, choices=ALCANCE_CHOICES)   # 1/2/3
    fuente = models.CharField(max_length=20, choices=FUENTE_CHOICES)    # AGRUPADOR GENERAL

    # DETALLE DEL TIPO DE CONSUMO (EJ: 'diesel_L', 'electricidad_red_kWh')
    consumo_tipo = models.CharField(max_length=60)

    # CANTIDAD Y UNIDAD DEL CONSUMO
    consumo_cantidad = models.DecimalField(max_digits=14, decimal_places=4)
    consumo_unidad = models.CharField(max_length=20)

    # FACTOR EN tCO2e POR UNIDAD (YA EN TONELADAS POR UNIDAD)
    factor_tco2e_por_unidad = models.DecimalField(max_digits=16, decimal_places=8)

    # RESULTADO CALCULADO EN tCO2e
    emisiones_tco2e = models.DecimalField(max_digits=16, decimal_places=6, blank=True, null=True)

    # TRAZABILIDAD
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comprobante = models.FileField(upload_to=upload_to_emisiones, blank=True, null=True)
    notas = models.TextField(blank=True)

    # MANAGER CON ALIAS
    objects = EmisionManager()

    class Meta:
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["pais", "fecha"]),
            models.Index(fields=["alcance", "fecha"]),
            models.Index(fields=["fuente", "fecha"]),
        ]
        ordering = ["-fecha", "-id"]

    # CALCULA SI FALTA EL RESULTADO
    def calcular_emisiones(self):
        if self.consumo_cantidad is not None and self.factor_tco2e_por_unidad is not None:
            # tCO2e = CANTIDAD * FACTOR(tCO2e/UNIDAD)
            self.emisiones_tco2e = (self.consumo_cantidad * self.factor_tco2e_por_unidad)

    def save(self, *args, **kwargs):
        if self.emisiones_tco2e is None:
            self.calcular_emisiones()
        super().save(*args, **kwargs)

    # ALIAS DE SOLO LECTURA PARA USAR EN TEMPLATES (NO SIRVE PARA QUERIES)
    @property
    def consumo(self):
        return self.consumo_cantidad

    @property
    def factor(self):
        return self.factor_tco2e_por_unidad

    @property
    def emisiones(self):
        return self.emisiones_tco2e

    def __str__(self):
        return f"{self.fecha.isoformat()} · {self.get_pais_display()} · {self.unidad_negocio or '-'} · {self.emisiones_tco2e} tCO2e"


# ============================================================
# 3) CARGAS DE CONSUMO (MANUAL O MASIVA)
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
# 4) SIMULACIONES (ENERGETICA O NORMATIVA)
# ============================================================

class Simulacion(models.Model):
    TIPO_CHOICES = [
        ("Energetica", "Transicion Energetica"),
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
# 5) INICIATIVAS DE MITIGACION
# ============================================================

class Iniciativa(models.Model):
    CATEGORIA_CHOICES = [
        ("Energia", "Energia"),
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
    reduccion_esperada = models.FloatField(help_text="tCO2e evitadas", blank=True, null=True)
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
# 6) REPORTES Y EXPORTACIONES
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
# 7) ALERTAS / NOTIFICACIONES
# ============================================================

class Alerta(models.Model):
    TIPO_CHOICES = [
        ("Incumplimiento", "Incumplimiento normativo"),
        ("Desviacion", "Desviacion de meta"),
        ("Error", "Error de carga o validacion"),
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
# 8) PERFIL DE USUARIO
# ============================================================

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    unidad_negocio = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=50, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to="perfiles/", blank=True, null=True)
    factor_emision=F('factor_tco2e_por_unidad')

    def __str__(self):
        return f"Perfil de {self.user.username}"
