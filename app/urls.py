from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('iniciar_sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('cerrar_sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    path('agricultores/', views.agricultores, name='agricultores'),
    path('agricultores/agregar/', views.agricultor_add, name='agricultor_add'),
    path('agricultores/<int:agricultor_id>/editar/', views.agricultor_edit, name='agricultor_edit'),
    path('precios/', views.precios, name='precios'),
    path('generar_tablas/', views.generar_tablas, name='generar_tablas'),
    path('generar_pronosticos', views.generar_pronosticos, name='generar_pronosticos'),
]