# canelo-software

Aplicación web para el mantenimiento de una base de datos de agricultores y precios de productos agricolas y ganaderos,
junto con la generacion de imagenes de tablas de precios segun la necesidad de los agricultores.

### La version actual permite:
- Ver los precios en la base de datos
- Subir archivos excel de precios de odepa para su inclusion en la base de datos
- Ver, agregar y modificar los agricultores en la base de datos
- Generar las imagenes de tablas de precios necesarias segun las necesidades de los agricultores de la base de datos

### Para correr el proyecto de manera local:

- Instalar Python **3.10** 

Se recomienda utilizar un entorno virtual (venv) para evitar errores de dependencias. Para usar un entrono vitual hay que:

- cd a la carpeta donde esta contenido el project django
- Crear un entorno vitrual: `py -m venv venv`
- Activar el entorno virtual: `.\venv\Scripts\activate in Windows`
- Instalar los requerimiento con pip: `pip install -r requirements.txt`

Luego:
- Preparar los cambios hechos a los modelos: `py manage.py makemigrations`
- Migrar los cambios a los modelos: `py manage.py migrate`
- Correr el servidor: `py manage.py runserver`

Si se quiere ocupar una Base de datos de postgres local:

- Modificar las credenciales en DATABASES en el archivo settings.py del proyecto.
