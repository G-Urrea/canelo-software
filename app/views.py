from itertools import product
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage

import unidecode
import json
import pandas as pd
import app.utils.pronostico as pronosticos
from datetime import datetime
import pytz
import os
import base64

from .models import Agricultor, Precio, Mercado, Producto, Region, Variedad
from .forms import AgricultorForm, ActualizacionPrecioForm
from .filters import PrecioFilter, AgricultorFilter

#vista para iniciar sesión como administrador
pd.options.mode.chained_assignment = None
def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.info(request, 'Usuario o contraseña es incorrecta')
        context = {}
        return render(request, 'app/login.html', context)

#cierre de sesion, devuelve a iniciar_sesión
def cerrar_sesion(request):
    logout(request)
    return redirect('iniciar_sesion')

#vista para la pagina de inicio
@login_required(login_url='iniciar_sesion')
def index(request):
    return render(request,'app/index.html')

#vista que permite ver la lista de todos los agricultores e ir a agregar o editar uno
@login_required(login_url='iniciar_sesion')
def agricultores(request):
    all_agricultores = Agricultor.objects.order_by('comuna__region', 'comuna')
    filtro_agricultor = AgricultorFilter(request.GET, queryset=all_agricultores)
    all_agricultores = filtro_agricultor.qs

    context = {
        'all_agricultores' : all_agricultores,
        'filtro_agricultor' : filtro_agricultor
    }
    return render(request, 'app/agricultores.html', context)

#vista que permite editar la informacion de un agricultor
@login_required(login_url='iniciar_sesion')
def agricultor_edit(request, agricultor_id):
    agricultor = Agricultor.objects.get(id=agricultor_id)
    form = AgricultorForm(instance=agricultor)
    if request.method == 'POST':
        form = AgricultorForm(request.POST, instance=agricultor)
        if form.is_valid():
            form.save()
            nombre_agricultor = form.cleaned_data.get('nombres') + ' ' + form.cleaned_data.get('apellidos') 
            messages.success(request, 'Se actualizaron los datos de ' + nombre_agricultor + ' correctamente')
            return redirect('agricultores')
    context = { 'form' : form }
    return render(request, 'app/agricultor_edit.html', context)

#vista que permite agregar a un nuevo agricultor ingresando su información
@login_required(login_url='iniciar_sesion')
def agricultor_add(request):
    form = AgricultorForm()
    if request.method == 'POST':
        form = AgricultorForm(request.POST)
        if form.is_valid():
            form.save()
            nombre_agricultor = form.cleaned_data.get('nombres') + ' ' + form.cleaned_data.get('apellidos') 
            messages.success(request, 'Se agrego correctamente al agricultor ' + nombre_agricultor)
            return redirect('agricultores')
    context = {'form' : form }
    return render(request, 'app/agricultor_add.html', context)

#vista que permite ver la lista de los ultimos precios subidos de las variedades de productos en los distintos mercados de la base de datos
#tambien permite subir actualizaciones de los precios en formato excel
@login_required(login_url='iniciar_sesion')
def precios(request):
    form = ActualizacionPrecioForm()
    if request.method == 'POST':
        form = ActualizacionPrecioForm(request.POST, request.FILES)
        print(form.is_valid,form.errors)
        print(form.cleaned_data.get('tipo'))
        if form.is_valid():
            form.save()
            tipo = form.cleaned_data.get('tipo')
            messages.success(request, 'Se actualizo correctamente los precios ' + tipo + 's')
            return redirect('precios')
    precios = Precio.objects.all()
    precios_agricolas = precios.filter(variedad__producto__tipo='agricola')
    precios_ganaderos = precios.filter(variedad__producto__tipo='ganadero')
    filtro_agricolas = PrecioFilter(request.GET, queryset=precios_agricolas)
    filtro_ganaderos = PrecioFilter(request.GET, queryset=precios_ganaderos)
    precios_agricolas = filtro_agricolas.qs
    precios_ganaderos = filtro_ganaderos.qs
    context = {
        'precios_agricolas' : precios_agricolas,
        'precios_ganaderos' : precios_ganaderos,
        'filtro_agricolas' : filtro_agricolas,
        'filtro_ganaderos' : filtro_ganaderos,
        'form' : form,
    }
    return render(request, 'app/precios.html', context)


# Elimina elementos en path que no se han modificado hoy
def eliminar_desactualizados(path):
    hoy = datetime.now(pytz.timezone('America/Santiago')).date()
    # Ver si hay imagenes creadas hoy, eliminar aquellas que no se han creado hoy
    for p, _, files in os.walk(f'{path}'):
        for name in files:
            path_file = os.path.join(p, name)
            fecha_modificacion = datetime.fromtimestamp((os.stat(path_file).st_mtime)).date()
            if hoy != fecha_modificacion:
                os.remove(path_file)

@csrf_exempt
def generar_pronosticos(request):
    # Archivo debe estar en path/media
    path = settings.MEDIA_ROOT
    
    if request.method == "GET":
        # Ver fecha
        hoy = datetime.now(pytz.timezone('America/Santiago')).date()
        nombre_archivo = f"pronostico.csv"
        
        # Generar df sólo una vez al día
        # Si no existe, se recopilan los datos
        if not os.path.exists(f'{path}/{nombre_archivo}'):
            df = pronosticos.get_pronosticos()
            df.to_csv(f'{path}/{nombre_archivo}', encoding='utf-8', index=False)
        else:
            if hoy == datetime.fromtimestamp((os.stat(f'{path}/{nombre_archivo}').st_mtime)).date():
                print('Estaba actualizado! :D')
                df = pd.read_csv(f'{path}/{nombre_archivo}',encoding='utf-8')
                df.fillna('', inplace=True)
            else:
                # El archivo no estaba actualizado
                df = pronosticos.get_pronosticos()
                df.to_csv(f'{path}/{nombre_archivo}', encoding='utf-8', index=False)
    
    
        tables = pronosticos.get_tablas_pronostico(df)
        ciudades = {}

        # Verificar que están los iconos y si no, actualizarlos
        pronosticos.actualizar_imagenes(df, f'{path}/iconos_pronostico')


        autorizar_descarga = []

        lista_ciudades = []
        hoy_str = hoy.strftime('%d_%m_%Y')
        for ciudad in tables:

            # Formatear temperatura para tablas
            temp = tables[ciudad]['temperatura'].apply(lambda y : pronosticos.format_temperatura(y) ).copy()
            tables[ciudad]['temperatura'] = temp

            temp = tables[ciudad]['fecha'].copy().apply(lambda x: "<br>".join(x.split(' ')))
            tables[ciudad]['fecha'] = temp

            json_records = tables[ciudad].reset_index().to_json(orient ='records', force_ascii=False)
            data = json.loads(json_records)
            ciudades[ciudad] = data

            nombre_imagen = f"pronostico_{ciudad.replace('/','_')}_{hoy_str}.png"

            lista_ciudades.append(ciudad)

            # Si existe la imagen
            if os.path.exists(f'{path}/pronosticos/{nombre_imagen}'):
                autorizar_descarga.append(False)
            else:
                autorizar_descarga.append(True)

            

        # Asegurarse que no hayan imagenes desactualizadas
        eliminar_desactualizados(f'{path}/pronosticos')

        # Verificar que haya imagenes 
        context = {
                'ciudades':ciudades,
                'lista_ciudades': json.dumps(lista_ciudades),
                'fecha': json.dumps(hoy_str),
                'autorizar' : json.dumps(autorizar_descarga)
                }
        return render(request, 'app/generar_pronostico.html', context)

    if request.method == 'POST':
         # Dejar imagenes en url, todas las tablas en una carpeta
        try:
            name = request.POST.get('name')
            img = request.POST.get('image')

            if not os.path.exists(f'{path}/pronosticos'):
                os.makedirs(f'{path}/pronosticos')
            
            with open(f'{path}/pronosticos/{name}', "wb") as fh:
                        fh.write(base64.b64decode(img))

        except Exception as e:
            print('Error:')
            print(e)
            print('Fallaste wachin')

            return HttpResponse('400')
        
        return HttpResponse('200')



#vista que genera las tablas de precio en html para ser descargadas en forma de imagen
@csrf_exempt
def generar_tablas(request):

    if request.method=="POST":
        path = settings.MEDIA_ROOT
        try:
            name = request.POST.get('name')
            img = request.POST.get('image')

            if not os.path.exists(f'{path}/tablas_precios'):
                os.makedirs(f'{path}/tablas_precios')

            
            with open(f'{path}/tablas_precios/{name}', "wb") as fh:
                        fh.write(base64.b64decode(img))
            print(f'Se guardó imagen: {name}')

        except Exception as e:
            print('Error:')
            print(e)
            print('Fallaste wachin')

            return HttpResponse('400')
        
        return HttpResponse('200')
    if request.method=="GET":
        hoy = datetime.now(pytz.timezone('America/Santiago')).date()
        hoy_str = hoy.strftime('%d_%m_%Y')

        path = settings.MEDIA_ROOT
        # Eliminar tablas de precios desactualizadas
        eliminar_desactualizados(f'{path}/tablas_precios')

        all_agricultores = Agricultor.objects.all()
        necesarias_agricolas = [] #lista de las tablas necesarias para precios agricultores (dadas por pares region producto)
        necesarias_ganaderos = [] #lista de las tablas necesarias para precios ganaderos (dadas por pares region mercado)
        for agricultor in all_agricultores:
            for region in agricultor.region_interes.all():
                for producto in agricultor.productos.filter(tipo='agricola'):
                    nueva_region_producto = [region, producto]
                    if not nueva_region_producto in necesarias_agricolas:
                        necesarias_agricolas.append(nueva_region_producto)
                for mercado in Mercado.objects.filter(region=region, tipo='ganadero'):
                    nueva_region_mercado = [region,mercado]
                    if not nueva_region_mercado in necesarias_ganaderos and agricultor.productos.filter(tipo='ganadero').exists():
                        necesarias_ganaderos.append(nueva_region_mercado)
        all_data_precios_agricolas = []
        all_data_precios_ganaderos =[]
        ids = []
        for region_producto in necesarias_agricolas:
            data_precios_agricolas = get_data_precios_agicolas(region_producto[0], region_producto[1])
            if len(data_precios_agricolas) > 0:
                div_id = unidecode.unidecode("_".join((region_producto[0].nombre + ' ' + region_producto[1].nombre).lower().split()))
                div_i = '<div id=' + div_id + ' style="overflow: hidden; width: 1080px;">'
                div_f = '</div>'
                all_data_precios_agricolas.append([region_producto[0], region_producto[1], data_precios_agricolas, [div_i,div_f]])
                ids.append(div_id)
        for region_mercado in necesarias_ganaderos:
            data_precios_ganaderos = get_data_precios_ganaderos(region_mercado[1])
            if len(data_precios_ganaderos) > 0:
                div_id = unidecode.unidecode("_".join((region_mercado[0].nombre + ' ' + region_mercado[1].nombre).lower().split()))
                div_i = '<div id=' + div_id + ' style="overflow: hidden; width: 1080px;">'
                div_f = '</div>'
                all_data_precios_ganaderos.append([region_mercado[1], data_precios_ganaderos, [div_i,div_f]])
                ids.append(div_id)

        # Revisar si imagenes fueron creadas:
        autorizar = []

        for id in ids:
            nombre_imagen = f'{id}_{hoy_str}.png'
            if os.path.exists(f'{path}/tablas_precios/{nombre_imagen}'):
                autorizar.append(False)
            else:
                autorizar.append(True)


        context = {
            'all_data_precios_agricolas' : all_data_precios_agricolas,
            'all_data_precios_ganaderos' : all_data_precios_ganaderos,
            'ids' : json.dumps(ids),
            'fecha': json.dumps(hoy_str),
            'autorizar': json.dumps(autorizar)
        }
        return render(request, 'app/generar_tablas.html', context)

#funcion auxiliar que obtiene los precios de todas las variedades de un producto agricolas en los dintintos mercados de una region
def get_data_precios_agicolas(a_region, a_producto):
    hoy = datetime.now(pytz.timezone('America/Santiago')).date()
    mercados = Mercado.objects.filter(region=a_region)
    variedades = Variedad.objects.filter(producto=a_producto)
    lista_mercado_precios = []
    for a_mercado in mercados:
        precios = Precio.objects.filter(mercado=a_mercado, variedad__in=variedades, fecha_subida=hoy)
        print(precios)
        if len(precios) > 0:
            lista_mercado_precios.append([a_mercado, precios])
    return lista_mercado_precios

#funcion auxiliar que obtiene los precios de todos los productos ganaderos en un mercado
def get_data_precios_ganaderos(a_mercado):
    hoy = datetime.now(pytz.timezone('America/Santiago')).date()
    precios = Precio.objects.filter(mercado=a_mercado, fecha_subida=hoy)
    return precios
#funcion auxiliar que obtiene los precios mas recientes de todos las variedades de productos
# def get_latest_precios():
#     precios = set()
#     for variedad in Variedad.objects.all():
#         for mercado in Mercado.objects.all():
#             if Precio.objects.filter(variedad=variedad, mercado=mercado).exists():
#                 precio = Precio.objects.filter(variedad=variedad, mercado=mercado).latest('fecha_subida')
#                 precios.add(precio.pk)
#     return Precio.objects.filter(pk__in=precios)