import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canelo_software.settings')
django.setup()

from app.models import Region, Comuna, Mercado
import pandas as pd

#Script para agregar las regiones con sus comunas y mercados a la base de datos

#funcion auxiliar que agrega a la base de datos una region con sus comunas y mercados correspondientes
def load_reg_com_mer(region, comunas, mercados_agricolas, mercados_ganaderos):
    nueva_region = Region.objects.create(nombre=region)
    nuevas_comunas = comunas.splitlines()
    for comuna in nuevas_comunas:
        nueva_comuna = Comuna(nombre=comuna, region=nueva_region)
        nueva_comuna.save()
    if type(mercados_agricolas) == str:
        nuevos_mercados = mercados_agricolas.splitlines()
        for mercado in nuevos_mercados:
            print(nueva_region)
            nuevo_mercado = Mercado(nombre=mercado, region=nueva_region, tipo='agricola')
            nuevo_mercado.save()
    if type(mercados_ganaderos) == str:
        nuevos_mercados = mercados_ganaderos.splitlines()
        for mercado in nuevos_mercados:
            print(nueva_region)
            nuevo_mercado = Mercado(nombre=mercado, region=nueva_region, tipo='ganadero')
            nuevo_mercado.save()

#funcion que carga todas las regiones con sus comunas y mercados correspondientes a la base de datos
def load_all_reg_com_mer(path):
    com_reg_mer_fer = pd.read_excel(
      path,
      header=None,
      names=['region','comunas','mercados_agricolas','mercados_ganaderos']
      )
    com_reg_mer_fer.apply(lambda row : load_reg_com_mer(row['region'], row['comunas'], row['mercados_agricolas'], row['mercados_ganaderos']), axis=1)


if __name__ == "__main__":
    path = 'static/media/regiones_comunas_mercados.xlsx'
    load_all_reg_com_mer(path)