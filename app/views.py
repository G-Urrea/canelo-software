from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import unidecode
import json

from .models import Agricultor, Precio, Mercado, Producto, Region, Variedad
from .forms import AgricultorForm, ActualizacionPrecioForm
from .filters import PrecioFilter, AgricultorFilter

#vista para iniciar sesión como administrador
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
    precios = get_latest_precios()
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

#vista que genera las tablas de precio en html para ser descargadas en forma de imagen
@csrf_exempt
def generar_tablas(request):
    all_agriucltores = Agricultor.objects.all()
    necesarias_agricolas = [] #lista de las tablas necesarias para precios agricultores (dadas por pares region producto)
    necesarias_ganaderos = [] #lista de las tablas necesarias para precios ganaderos (dadas por pares region mercado)
    for agricultor in all_agriucltores:
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
    context = {
        'all_data_precios_agricolas' : all_data_precios_agricolas,
        'all_data_precios_ganaderos' : all_data_precios_ganaderos,
        'ids' : json.dumps(ids),
    }
    return render(request, 'app/generar_tablas.html', context)

#funcion auxiliar que obtiene los precios de todas las variedades de un producto agricolas en los dintintos mercados de una region
def get_data_precios_agicolas(a_region, a_producto):
    mercados = Mercado.objects.filter(region=a_region)
    variedades = Variedad.objects.filter(producto=a_producto)
    lista_mercado_precios = []
    for a_mercado in mercados:
        lista_precios = []
        for a_variedad in variedades:
            if Precio.objects.filter(mercado=a_mercado,variedad=a_variedad).exists():
                a_precio = Precio.objects.filter(mercado=a_mercado,variedad=a_variedad).latest('fecha_subida')
                lista_precios.append(a_precio)
        if len(lista_precios) > 0:
            lista_mercado_precios.append([a_mercado, lista_precios])
    return lista_mercado_precios

#funcion auxiliar que obtiene los precios de todos los productos ganaderos en un mercado
def get_data_precios_ganaderos(a_mercado):
    lista_precios = []
    for variedad in Variedad.objects.all():
        if Precio.objects.filter(variedad=variedad, mercado=a_mercado).exists():
            precio = Precio.objects.filter(variedad=variedad, mercado=a_mercado).latest('fecha_subida')
            lista_precios.append(precio)
    return lista_precios

#funcion auxiliar que obtiene los precios mas recientes de todos las variedades de productos
def get_latest_precios():
    precios = set()
    for variedad in Variedad.objects.all():
        for mercado in Mercado.objects.all():
            if Precio.objects.filter(variedad=variedad, mercado=mercado).exists():
                precio = Precio.objects.filter(variedad=variedad, mercado=mercado).latest('fecha_subida')
                precios.add(precio.pk)
    return Precio.objects.filter(pk__in=precios)