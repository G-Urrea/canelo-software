import django_filters
from .models import *

#filtro para filtrar precios en la vista de precios segun region y producto
class PrecioFilter(django_filters.FilterSet):
    class Meta:
        model = Precio
        fields = ['mercado__region', 'variedad__producto']

#filtro para filtar agricutores en la vista de agricultores segun comuna region propia, region de interes y productos
class AgricultorFilter(django_filters.FilterSet):
    class Meta:
        model = Agricultor
        fields = ['comuna', 'comuna__region', 'region_interes', 'productos']