import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canelo_sofware.settings')

import app.models
import pandas as pd


#Script para actualizar los precios de las variedades de productos en la base de datos a partir de los excels extraidos de ODEPA

#funcion auxiliar para eliminar espacios duplicados, iniciales o finales en un string
def dup_space_stripper(a_string):
    return ' '.join(a_string.split())

#funcion auxiliar que permite obtener el nombre de un producto o su variedad a partir de un string
def splitter(a_string, tipo):
  producto_variedad = a_string.split()
  if tipo == 'producto':
    return producto_variedad[0]
  elif tipo == 'variedad':
    if len(producto_variedad) == 1:
      return ''
    else:
      return ' '.join(producto_variedad[1:])

#funcion auxiliar que deja en un formato trabajable el archivo excel de precios de productos agricolas entregandolo como un dataframe de pandas
def formatear_precios_agricolas(path):
  precios = pd.read_excel(
      path,
      header=None,
      names=['mercado','producto','variedad','calidad','volumen','precio_minimo','precio_maximo','precio_promedio_ponderado','unidad_comercializacion']
      )
  precios = precios[6:][:-1] #en la fila 6 comienzan los productos y la ultima fila es la fuente
  precios = precios.drop(['volumen','precio_promedio_ponderado'], axis=1) #elimina las columnas que no sirven

  precios['variedad'].replace({"Sin especificar": ""}, inplace=True) #se quitan las variedades sin especificar

  return precios

#funcion auxiliar que actualiza en la base de datos un precio de una variedad de producto agricola en un mercado
def update_precio_agricola(a_mercado, a_producto, a_variedad, a_calidad, a_precio_minimo, a_precio_maximo, a_unidad_comercializacion, a_fecha_subida):
    if not app.models.Mercado.objects.filter(nombre=a_mercado).exists():
        mercado = app.models.Mercado.objects.create(nombre=a_mercado, tipo='agricola')
    else:
        mercado = app.models.Mercado.objects.get(nombre=a_mercado)

    if not app.models.Producto.objects.filter(nombre=a_producto).exists():
        producto = app.models.Producto.objects.create(nombre=a_producto, tipo='agricola')
    else:
        producto = app.models.Producto.objects.get(nombre=a_producto)
    
    if not app.models.Variedad.objects.filter(nombre=a_variedad, calidad=a_calidad, producto=producto).exists():
        variedad = app.models.Variedad.objects.create(nombre=a_variedad, calidad=a_calidad, producto=producto)
    else:
        variedad = app.models.Variedad.objects.get(nombre=a_variedad, calidad=a_calidad, producto=producto)

    #el codigo comentado guarda el nuevo precio para una variedad en un mercado como un objeto independiente de el anteriormente guardado, debido a las limitaciones de filas en heroku no se utilizó
    #app.models.Precio.objects.create(variedad=variedad, mercado=mercado, precio_minimo=a_precio_minimo, precio_maximo=a_precio_maximo, unidad=a_unidad_comercializacion, fecha_subida=a_fecha_subida)

    if not app.models.Precio.objects.filter(variedad=variedad, mercado=mercado).exists():
        app.models.Precio.objects.create(variedad=variedad, mercado=mercado, precio_minimo=a_precio_minimo, precio_maximo=a_precio_maximo, unidad=a_unidad_comercializacion, fecha_subida=a_fecha_subida)
    else:
        precio = app.models.Precio.objects.filter(variedad=variedad, mercado=mercado)
        precio.update(precio_minimo=a_precio_minimo, precio_maximo=a_precio_maximo, unidad=a_unidad_comercializacion, fecha_subida=a_fecha_subida)

    return

#funcion que actualiza en la base de datos todos los precios agricolas
def update_all_precios_agricolas(path, a_fecha_subida):
    nuevos_precios = formatear_precios_agricolas(path)
    nuevos_precios.apply(
        lambda row : update_precio_agricola(
            row['mercado'], row['producto'], row['variedad'], row['calidad'], row['precio_minimo'], row['precio_maximo'], row['unidad_comercializacion'], a_fecha_subida),
            axis=1
            )
    return

#funcion auxiliar que deja en un formato trabajable el archivo excel de precios de productos ganaderos entregandolo como un dataframe de pandas
def formatear_hoja_ganaderos(path, sheet_name):
  inicio = 8
  if sheet_name == 'Precio promedio':
    dato = 'precio_promedio'
  elif sheet_name == 'Promedio (5 primeros precios)':
    dato = 'precio_primeros_5'
  elif sheet_name == 'Número de cabezas':
    dato = 'numero_cabezas'
    inicio = 6
  tabla = pd.read_excel(
    path,
    sheet_name=sheet_name,
    header=None,
    names=['feria', 'comuna', 'fecha', 'Novillo Gordo', 'Novillo Engorda', 'Vaca Gorda', 'Vaca Engorda', 'Vaquilla Gorda', 'Vaquilla Engorda', 'Toros', 'Terneros', 'Terneras', 'Cerdos', 'Lanares', 'Caballos']
  )
  tabla = tabla[inicio:][:-1] 
  tabla['feria_comuna'] = tabla[['feria','comuna']].agg(' '.join, axis=1)
  tabla['feria_comuna'] = tabla['feria_comuna'].apply(dup_space_stripper)
  tabla = tabla.drop(['feria','comuna','fecha'], axis=1)

  tabla = tabla.melt('feria_comuna', var_name='ganado_variedad', value_name=dato)
  tabla['ganado'] = tabla.apply(lambda row: splitter(row['ganado_variedad'], 'producto'), axis=1)
  tabla['variedad'] = tabla.apply(lambda row: splitter(row['ganado_variedad'], 'variedad'), axis=1)
  tabla = tabla.drop(['ganado_variedad'], axis=1)
  tabla.reset_index(drop=True, inplace=True)
  return tabla

#funcion auxiliar que agrega las columnas de precio promediio y numero de cabezas a los registros
def formatear_precios_ganaderos(path):
  df_precio_promedio = formatear_hoja_ganaderos(path, 'Precio promedio')
  df_numero_cabezas = formatear_hoja_ganaderos(path, 'Número de cabezas')

  df_final = pd.concat([df_precio_promedio,df_numero_cabezas],axis=1)
  df_final = df_final.loc[:,~df_final.columns.duplicated()]

  return df_final

#funcion auxiliar que actualiza en la base de datos un precio de una variedad de producto ganadero en un mercado
def update_precio_ganadero(a_feria_comuna, a_ganado, a_variedad, a_precio_promedio, a_numero_cabezas, a_fecha_subida):
    if a_precio_promedio == 0:
        return

    if not app.models.Mercado.objects.filter(nombre=a_feria_comuna).exists():
        mercado = app.models.Mercado.objects.create(nombre=a_feria_comuna, tipo='ganadero')
    else:
        mercado = app.models.Mercado.objects.get(nombre=a_feria_comuna)

    if not app.models.Producto.objects.filter(nombre=a_ganado).exists():
        producto = app.models.Producto.objects.create(nombre=a_ganado, tipo='ganadero')
    else:
        producto = app.models.Producto.objects.get(nombre=a_ganado)

    if not app.models.Variedad.objects.filter(nombre=a_variedad, producto=producto).exists():
        variedad = app.models.Variedad.objects.create(nombre=a_variedad, producto=producto)
    else:
        variedad = app.models.Variedad.objects.get(nombre=a_variedad, producto=producto)

    #el codigo comentado guarda el nuevo precio para una variedad en un mercado como un objeto independiente de el anteriormente guardado, debido a las limitaciones de filas en heroku no se utilizó
    #app.models.Precio.objects.create(variedad=variedad, mercado=mercado, precio_promedio=a_precio_promedio, numero_cabezas=a_numero_cabezas, fecha_subida=a_fecha_subida)

    if not app.models.Precio.objects.filter(variedad=variedad, mercado=mercado).exists():
        app.models.Precio.objects.create(variedad=variedad, mercado=mercado, precio_promedio=a_precio_promedio, numero_cabezas=a_numero_cabezas, fecha_subida=a_fecha_subida)
    else:
        precio = app.models.Precio.objects.filter(variedad=variedad, mercado=mercado)
        precio.update(precio_promedio=a_precio_promedio, numero_cabezas=a_numero_cabezas, fecha_subida=a_fecha_subida)

    return

#funcion que actualiza en la base de datos todos los precios ganaderos
def update_all_precios_ganaderos(path, a_fecha_subida):
    nuevos_precios = formatear_precios_ganaderos(path)
    nuevos_precios.apply(
        lambda row : update_precio_ganadero(
            row['feria_comuna'], row['ganado'], row['variedad'], row['precio_promedio'], row['numero_cabezas'], a_fecha_subida),
            axis=1
            )
    return