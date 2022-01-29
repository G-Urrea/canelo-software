from django.db import models
from django.db.models.fields import BooleanField, DateField, DateTimeField, IntegerField
from django.db.models.fields.related import ForeignKey, ManyToManyField

from update_precio import update_all_precios_agricolas, update_all_precios_ganaderos

# Modelos que representa a las region de Chile.
class Region(models.Model):
    nombre = models.CharField(max_length=(100), unique=True)

    def __str__(self):
        return self.nombre

# Modelos que representa las comuna de Chile. Esta asociados a una cierta region
class Comuna(models.Model):
    nombre = models.CharField(max_length=(100), unique=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, blank=True)

    def __str__(self):
        return self.nombre

#Modelo que representa los mercado donde se venden los productos. Estan asociado a una cierta region
class Mercado(models.Model):
    nombre = models.CharField(max_length=(100), unique=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, blank=True, null=True)
    TIPO_PRODUCTO_CHOICES = (
        ('agricola', 'Agrícola'),
        ('ganadero', 'Ganadero'),
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_PRODUCTO_CHOICES,
    )

    def __str__(self):
        return self.nombre

#Modelo que representa una producto. Segun su tipo puede ser un producto agricola o ganadero. Ej: lechuga
class Producto(models.Model):
    nombre = models.CharField(max_length=50)
    TIPO_PRODUCTO_CHOICES = (
        ('agricola', 'Agrícola'),
        ('ganadero', 'Ganadero'),
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_PRODUCTO_CHOICES,
    )

    def __str__(self):
        return '{}'.format(self.nombre)

#Modelo que representa las variedades y calidades especificas de productos. Ej: lechuga escarola primera
class Variedad(models.Model):
    nombre = models.CharField(max_length=50)
    calidad = models.CharField(max_length=50)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, blank=True)
    def __str__(self):
        return '{} {} {}'.format(self.producto, self.nombre, self.calidad)

#Modelo que representa a los agricultores con sus productos y regiones de interes
class Agricultor(models.Model):
    telefono = models.CharField(max_length=15)
    nombres = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    comuna = models.ForeignKey(Comuna, on_delete=models.PROTECT, blank=True)
    HORARIO_ENVIO_CHOICES = (
        ('todo_el_dia', 'Todo el día'), # 9hrs a 21hrs
        ('manana', 'Mañana'), # 9hrs
        ('tarde', 'Tarde'), # 14hrs
        ('noche', 'Noche'), # 20hrs
    )
    horario_envio = models.CharField(
        max_length=15,
        choices=HORARIO_ENVIO_CHOICES,
    )
    productos = models.ManyToManyField(Producto)
    region_interes = models.ManyToManyField(Region)
    SEGMENTO_CHOICES = (
        ('pequena_subsistencia', 'Pequeña Subsistencia'),
        ('pequena_transicion', 'Pequeña Transición'),
        ('mediano', 'Mediano'),
        ('grande', 'Grande'),
    )
    segmento = models.CharField(
        max_length=50,
        choices=SEGMENTO_CHOICES,
    )
    fecha_primera_entrevista = models.DateField()

    def __str__(self):
        return '{} {}: {}'.format(self.nombres, self.apellidos, self.telefono)

#Modelo que representan los precios de distintas variedades de productos. Estan asociados a una variedad y un mercado
class Precio(models.Model):
    variedad = models.ForeignKey(Variedad, on_delete=models.PROTECT, blank=True)
    mercado = models.ForeignKey(Mercado, on_delete=models.PROTECT, blank=True)
    precio_minimo = models.IntegerField(blank=True, null=True) #solo agricolas
    precio_maximo = models.IntegerField(blank=True, null=True) #solo agricolas
    unidad = models.CharField(max_length=50, blank=True, null=True) #solo agricolas
    precio_promedio = models.IntegerField(blank=True, null=True) #solo ganaderos
    numero_cabezas = models.IntegerField(blank=True, null=True) #solo ganaderos
    fecha_subida = models.DateField()
    def __str__(self):
        if self.precio_promedio is None:
            return '{} > {}: {} - {}'.format(str(self.mercado), str(self.variedad), self.precio_minimo, self.precio_maximo)
        else:
            return '{} > {}: {} , {}'.format(str(self.mercado), str(self.variedad), self.precio_promedio, self.numero_cabezas)

#Modelo que almacena los archivos excel conteniendo los precios de los productos y sus variedades en los mercados mayoristas
class ActualizacionPrecio(models.Model):
    TIPO_CHOICES = [
        ('agricola' , 'Agrícola'),
        ('ganadero', 'Ganadero'),
    ]
    tipo = models.CharField(
        max_length=(50),
        choices=TIPO_CHOICES,
        blank=True
    )
    archivo = models.FileField()
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super(ActualizacionPrecio, self).save(*args, **kwargs)
        if self.tipo == 'agricola':
            update_all_precios_agricolas(self.archivo.path, self.fecha_subida)
        if self.tipo == 'ganadero':
            update_all_precios_ganaderos(self.archivo.path, self.fecha_subida)