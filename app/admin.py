from django.contrib import admin

from .models import Region, Comuna, Mercado, Producto, Variedad, Agricultor, Precio, ActualizacionPrecio

admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Mercado)
admin.site.register(Producto)
admin.site.register(Variedad)
admin.site.register(Agricultor)
admin.site.register(Precio)
admin.site.register(ActualizacionPrecio)
