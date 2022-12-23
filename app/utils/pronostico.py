import requests
import urllib.request
import html
import json
import pandas as pd
import os
from django.conf import settings

# Retorna dataframe con los pronosticos actualizados
def get_pronosticos():
  jason_link = 'http://archivos.meteochile.gob.cl/portaldmc/meteochile/js/pronostico.json'
  with urllib.request.urlopen(jason_link) as url:
    # Obtener JSON, decodificar y transformar a diccionario python
    html_response = url.read()
    encoding = url.headers.get_content_charset('utf-8')
    decoded_html = html_response.decode(encoding)
    decoded_html = html.unescape(decoded_html) 
    data = json.loads(decoded_html)

  cols_horarios = ['madrugada',	'mañana',	'tarde','noche']
  cols_info = ['ciudad', 'redaccion'] # Info Común para cualquier día
  cols_info_diaria = ['fecha', 'temperatura'] # Info distinta por día
  cols_info_multiple = ['texto', 'icono'] # Info para cada horario en un día

  # Diccionario que se convertirá en el dataframe
  dict_df = {}

  # Crear columnas para tabla informativa
  # Info común
  for c in cols_info+cols_info_diaria:
    dict_df[c] = []
  # Info que depende del horario
  for c in cols_info_multiple:
    for h in cols_horarios:
      dict_df[f'{c}_{h}'] = []

  # Rellenar con los datos obtenidos

  for x in data['Pronostico']:

    # Por cada día de la semana
    for i in range(5):
      # Añadir info común de cada día
      for c in cols_info:
        dict_df[c].append(x[c])
      # Añadir info diaria
      for c in cols_info_diaria:
        dict_df[c].append(x[c][i])

      # Para textos e iconos
      for c in cols_info_multiple:
          # Para el día actual
          lista_dia = x[c][i]
          # Por cada horario
          for j in range(len(cols_horarios)):
            # Añadir iconos y texto de cada horario
            dict_df[f'{c}_{cols_horarios[j]}'].append(lista_dia[j])

  return pd.DataFrame(dict_df)

# Retorna diccionario con tablas de pronostico por comuna
def get_tablas_pronostico(df):
  tablas = {}
  ciudades = df['ciudad'].unique()
  # Se crea una tabla para cada ciudad
  for ciudad in ciudades:
    df_temp = df[df['ciudad']==ciudad]
    tablas[ciudad] = df_temp

  return tablas

# Formateo de temperatura para tablas
def format_temperatura(s):
  lista_split = s.split('/')
  return "<br>".join(list(map(lambda x: f'{x} °C' if len(x)>0 else '-', lista_split)))
# Descarga imagenes necesarias para las tablas, en caso de no tenerlas
def actualizar_imagenes(df, folder='media'):

  # Obtener nombre de iconos
  iconos = []
  cols_horarios = ['madrugada',	'mañana',	'tarde','noche']
  for hora in cols_horarios:
    iconos += list(df[f'icono_{hora}'].unique())
  iconos  = list(set(iconos))
  iconos = [x for x in iconos if len(x)>0]

  # Crear directorio en caso de que no exista.
  if not os.path.exists(folder): 
    os.makedirs(folder)


  for icono in iconos:
    # Si la imagen no existe en el directorio, se descarga
    if not os.path.exists(f'{folder}/{icono}'):
      print(f'Descargando {icono}...')
      try:
        img_data = requests.get(f'https://archivos.meteochile.gob.cl/portaldmc/localJS/img/clima_dark/{icono}').content
          
        with open(f'{folder}/{icono}', 'wb') as handler:
            handler.write(img_data)
      except:
        print('No se pudo descargar el archivo')
    

    
if __name__ == "__main__":
        path = settings.MEDIA_ROOT
        df = get_pronosticos()
        actualizar_imagenes(df, f'{path}/iconos_pronostico')