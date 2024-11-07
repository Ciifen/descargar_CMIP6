'''
El siguiente código fuente forma parte de los desarrollos realizados
por el "Centro Internacional para la Investigación del Fenómeno de El Niño
(CIIFEN)" dentro del Proyecto ENANDES “Mejora de la capacidad de adaptación
de las comunidades andinas a través de los servicios climáticos”

La reproducción, publicación, divulgación, copia o traspaso de parte
del mismo o su totalidad está totalmente prohibida y restringida.
Para ello se debe tener autorización formal previa de parte 
de las instituciones participantes del proyecto:
- Centro Internacional para la Investigación del Fenómeno de El Niño (CIIFEN)
- Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM) - Colombia
- Servicio Nacional de Meteorología e Hidrología del Perú (SENAMHI)
- Dirección Meteorológica de Chile

Script desarrollado por Ing. MSc. Guillermo Eduardo Armenta - 2024
Especialista en Climatología. Email: motsvanska@gmail.com

Este script realiza la descarga de los datos del CMIP6, para una zona delimitada
definida por el usuario. La descarga se hace por modelo, variable, temporalidad 
y escenario, para un intervalo de años requerido.

NOTA: Este script invoca a otro llamado "scriptDescargaDatosModelosCMIP6-v2.py",
por lo tanto, ambos scripts se deben tener en la misma carpeta

Para su uso, se deben realizar unos pasos de una sola vez (es decir, que se realizan
solamente la primera vez que se vaya a utilizar el script, y luego no es necesario 
volver a hacerlos -a excepción del paso 2-). Los pasos son los siguientes:
1. Se crea un entorno de trabajo bajo "Conda", a través del siguiente comando
   (en este ejemplo el entorno se llama "DescargaCMIP6"):
      conda create --name DescargaCMIP6
2. Una vez creado el entorno, el mismo se debe activar con el siguiente comando:
      conda activate DescargaCMIP6
3. Con este entorno activado (en la terminal de Conda aparece a la izquerda el nombre dado),
   se deben instalar unos paquetes para que el script funcione, y su instalación se realiza
   mediante el siguiente comando:
      conda install -c conda-forge esgf-pyclient xarray scipy netcdf4 rasterio matplotlib pathlib cartopy
'''

# A continuación, se definen los parámetros que el usuario modifica para 
# descargar los datos que requiera. Se indican los posibles valores de éstos,
# los cuales se deben escribir tal cual se muestran allí.
# NOTAS IMPORTANTES:
#   1. Este script invoca a otro llamado "scriptDescargaDatosModelosCMIP6-v2.py",
#      por lo tanto, ambos scripts se deben tener en la misma carpeta para
#      que funcione
#   2. Esta versión del script funciona únicamente para descargar los datos
#      de un intervalo de años de sólo un escenario, de sólo una variable, 
#      de sólo una temporalidad -diaria o mensual- y de un sólo modelo
#   3. Esta versión del script está elaborada para correr en Python versión 3.9 
#      y posteriores. Está probada para correr bajo ambientes Linux principalmente.
#   4. Recordar primero activar el entorno creado en los pasos mencionados en la
#      descripción del código al inicio (conda activate DescargaCMIP6)
#   5. El script en su ejecución muestra algunos mensajes de advertencia (warnings)
#      en inglés, se puede hacer caso omiso de ellos
#   6. El script está probado y funcional para los 4 modelos seleccionados
#      a lo largo del trabajo realizado en la "CONSULTORÍA PARA REALIZAR 
#      LA REVISIÓN BIBLIOGRÁFICA Y VERIFICACIÓN DE CUMPLIMIENTO DE LOS CRITERIOS
#      SELECCIONADOS PARA LA PRIORIZACIÓN DE LOS MODELOS DE PROYECCIONES 
#      DE CAMBIO CLIMÁTICO PARA LOS PAÍSES DEL OESTE DE SUDAMÉRICA – OSA",
#      realizada por el Ing. MSc. Guillermo Eduardo Armenta para el CIIFEN.
#      Para otros modelos diferentes no se garantiza su correcto funcionamiento.
#   7. Los servidores del CMIP6 suelen fallar en ocasiones. Si la descarga
#      no se realiza (es decir no se generó nigún archivo), por favor intentar 
#      en otra ocasión más adelante (dar un día de espera al menos)
#   8. El nombre de los archivos a descargar está compuesto de la siguiente forma:
#        "[Nombre de la variable climática]_[Escala temporal (diaria/mensual)]_
#        [Escenario SSP]_[Modelo del CMIP6]_[Año de datos buscado]_[Nombre dado
#        a la zona para la cual se descargan los datos].nc"
#      Todos los valores de los parámetros mencionados anteriormente entre []
#      se muestran en la sección de las variables definidas por el usuario, y estos
#      archivos quedan almacenados en la carpeta definida en la variable "rutasalidas"


# Librerías de Python necesarias para el funcionamiento del script
# NOTA: Se deben tener instaladas previamente, siguiendo los pasos mencionados
#       en la descripción del código al inicio

# ---NO MODIFICAR ESTAS LÍNEAS---
from pathlib import Path
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cf
# ---FIN LIBRERÍAS NECESARIAS---


#--VARIABLES DEFINIDAS POR EL USUARIO--

# Se define el modelo para el cual se requieren los datos
# Posibles valores: 'MPI-ESM1-2-HR', 'MRI-ESM2-0', 'CMCC-ESM2', 'GFDL-ESM4'
modelo='MPI-ESM1-2-HR'

# Se define el escenario para el cual se desean descargar los datos
# Posibles valores: 'historical', 'ssp126', 'ssp245', 'ssp370', 'ssp585'
escenario='ssp370'

# Se define la variable climática a descargar 
# (por el momento el script solamente funciona con las variables en superficie)
# Posibles valores: 'tas' (temperatura media), 'pr' (precipitación),
#                   'tasmax' (temperatura máxima), 'tasmin' (temperatura mínima)
varclim='tas'

# Se define la resolución temporal de los datos a descargar
# Posibles valores: 'day' (diaria), 'mon' (mensual)
frecuencia='mon'

# Como el script funciona para descargar los datos para un rango de años,
# se definen estos valores, colocando el año inicial en la variable "anyoinibuscado"
# y el año final en la variable "anyofinbuscado"
# Si los años a buscar están en el escenario de los datos históricos, éstos van
# desde 1850 hasta 2014. Si son en los escenarios SSP futuros, éstos van desde 2015
# hasta 2100
anyoinibuscado=2041
anyofinbuscado=2060

# Se define la zona para la cual se descargarán los datos:
#   lonmin: Coordenada geográfica de longitud oeste de la zona
#   lonmax: Coordenada geográfica de longitud este de la zona
#   latmin: Coordenada geográfica de latitud sur de la zona
#   latmax: Coordenada geográfica de latitud norte de la zona
#   nombrezona: El nombre del área a seleccionar 
#               (para el nombre del archivo a descargar)
# NOTA: Las coordenadas deben ser geográficas (longitud, latitud),
#       y éstas deben ser en decimales (no en grados, minutos y segundos).
#       Y para las coordenadas de longitud, éstas deben estar en el formato
#       -180 a 180 (es decir, las coordenadas oestes son en valores negativos)
#
# (Este ejemplo es para Sur y Centroamérica y el Caribe)
lonmin=-90
lonmax=-30
latmin=-60
latmax=20
nombrezona='Latinoamerica'

# Se define la carpeta en la que quedará almacenado el archivo NetCDF a generar
# (se coloca la ruta completa)
rutasalidas = Path("/mnt/ed616187-6f4d-404b-94f6-670ca5b49fbc/CIIFEN/1")

#--FIN DE LAS VARIABLES DEFINIDAS POR EL USUARIO--


#----NO MODIFICAR EL SCRIPT DE AQUÍ EN ADELANTE----

## Agregar lo de la validación de las coordenadas!

# Primero se validan las coordenadas de longitud y latitud
# (es decir, que la coordenada oeste de longitud de la zona 
# no sea mayor que la coordenada este, y que la coordenada 
# de latitud sur no sea mayor que la coordenada norte)

if( (lonmin>=lonmax) or (latmin>=latmax) ):
    print("Error con las coordenadas de la zona:")
    if(lonmin>=lonmax):
        print("La coordenada de longitud oeste ("+str(lonmin)+") es mayor o igual que la coordenada de longitud este ("+str(lonmax)+")")
    if(latmin>=latmax):
        print("La coordenada de latitud sur ("+str(latmin)+") es mayor o igual que la coordenada de latitud norte ("+str(latmax)+")")
    exit(1)
else:
    if( (anyoinibuscado>anyofinbuscado) ):
        print("Error con el rango de años dado: El año inicial ("+str(anyoinibuscado)+") es mayor que el año final ("+str(anyofinbuscado)+")")
        exit(1)
    else:    
        # --Estas líneas son para colocar la letra en el plot de las coordenadas 
        # de la zona para la cual se descargarán los datos--
        if(lonmin==0):
            zonalonmin=''
        else:
            if(lonmin<0):
                zonalonmin='W'
            else:
                zonalonmin='E'

        if(lonmax==0):
            zonalonmax=''
        else:
            if(lonmax<0):
                zonalonmax='W'
            else:
                zonalonmax='E'

        if(latmin==0):
            zonalatmin=''
        else:
            if(latmin<0):
                zonalatmin='S'
            else:
                zonalatmin='N'

        if(latmax==0):
            zonalatmax=''
        else:
            if(latmax<0):
                zonalatmax='S'
            else:
                zonalatmax='N'
        #--

        # Se crea el plot de la zona para la cual se descargarán los datos
        ax = plt.axes(projection=ccrs.Mercator())
        ax.set_extent([lonmin, lonmax, latmin, latmax])
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
        ax.add_feature(cf.COASTLINE)
        ax.add_feature(cf.LAND)
        ax.add_feature(cf.BORDERS)
        plt.title('Nombre Zona: '+nombrezona+' (Longitud: '+str(abs(lonmin))+zonalonmin+' a '+str(abs(lonmax))+zonalonmax+', Latitud: '+str(abs(latmin))+zonalatmin+' a '+str(abs(latmax))+zonalatmax+')\n')
        plt.annotate('(Para continuar el proceso cierre esta ventana)', (0,0), (-20, -20), xycoords='axes fraction', textcoords='offset points', va='top')
        plt.show()
    
        for anyo in range(int(anyoinibuscado),(int(anyofinbuscado)+1)):
            os.system("python3 scriptDescargaDatosModelosCMIP6-v2.py "+modelo+" "+escenario+" "+varclim+" "+frecuencia+" "+str(anyo)+" "+str(lonmin)+" "+str(lonmax)+" "+str(latmin)+" "+str(latmax)+" "+nombrezona+" "+str(rutasalidas)+"")

#----FIN----
