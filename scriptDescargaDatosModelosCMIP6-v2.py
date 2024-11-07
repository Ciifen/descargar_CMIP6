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
definida por el usuario. La descarga se hace por modelo, variable, temporalidad,
escenario y año de datos requerido.

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
#   1. Este script es invocado por otro llamado "descargarVariosAnyosDatosModelosCMIP6-v1.py",
#      por lo tanto, ambos scripts se deben tener en la misma carpeta para que funcione
#   2. Esta versión del script funciona únicamente para descargar los datos
#      de sólo un año, de sólo un escenario, de sólo una variable, 
#      de sólo una temporalidad -diaria o mensual- y de un sólo modelo.
#      Estos parámetros se definen en el script "descargarVariosAnyosDatosModelosCMIP6-v1.py"
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
#   8. El nombre del archivo a descargar está compuesto de la siguiente forma:
#        "[Nombre de la variable climática]_[Escala temporal (diaria/mensual)]_
#        [Escenario SSP]_[Modelo del CMIP6]_[Año de datos buscado]_[Nombre dado
#        a la zona para la cual se descargan los datos].nc"
#      Todos los valores de los parámetros mencionados anteriormente entre []
#      se muestran en la sección de las variables definidas por el usuario, y estos
#      archivos quedan almacenados en la carpeta definida en la variable "rutasalidas",
#      definida en el script "descargarVariosAnyosDatosModelosCMIP6-v1.py"


# Librerías de Python necesarias para el funcionamiento del script
# NOTA: Se deben tener instaladas previamente, siguiendo los pasos mencionados
#       en la descripción del código al inicio

# ---NO MODIFICAR ESTAS LÍNEAS---
import pyesgf
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cf
from pyesgf.search import SearchConnection
import sys
# ---FIN LIBRERÍAS NECESARIAS---

modelo=sys.argv[1]
escenario=sys.argv[2]
varclim=sys.argv[3]
frecuencia=sys.argv[4]
anyobuscado=int(sys.argv[5])
lonmin=float(sys.argv[6])
lonmax=float(sys.argv[7])
latmin=float(sys.argv[8])
latmax=float(sys.argv[9])
nombrezona=sys.argv[10]
rutasalidas=sys.argv[11]

#----NO MODIFICAR EL SCRIPT DE AQUÍ EN ADELANTE----

# Aquí se define la variable con el nombre del archivo de salida
nomarchsalida=varclim+'_'+frecuencia+'_'+escenario+'_'+modelo+'_'+str(anyobuscado)+'_'+nombrezona+'.nc'

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
    
    # Inicia el proceso de descarga de los datos como tal

    # Se define la página de la cual se buscarán y descargarán los datos
    conn = SearchConnection('https://esgf-node.llnl.gov/esg-search', distrib=True)

    # Se definen los parámetros de la consulta a realizar para encontrar 
    # los archivos disponibles para el modelo, variable climática, escenario 
    # y frecuencia temporal definidos
    ctx = conn.new_context(
        project='CMIP6',
        source_id=modelo,
        experiment_id=escenario,
        variable=varclim,
        frequency=frecuencia,
        variant_label='r1i1p1f1',
        data_node='esgf.ceda.ac.uk',
        facets='*')
    ctx.hit_count

    # Se realiza la consulta como tal
    result = ctx.search()[0]

    # Y se obtiene el listado de archivos disponibles
    files = result.file_context().search()

    # Acá se establece la cantidad de tiempos que debem traerse del año buscado,
    # según la temporalidad definida (si son datos diarios se traen 365 o 366 días,
    # si son mensuales se traen los 12 meses) 
    if(frecuencia=='day'):
        temporalidad1=365
        temporalidad2=366
        restemp='diarios'
    else:
        temporalidad1=12
        temporalidad2=12
        restemp='mensuales'

    # Se muestran en pantalla los parámetros establecidos para la búsqueda y descarga
    # del archivo a buscar
    print("Realizando la búsqueda y descarga de los datos "+restemp+" de "+varclim+",")
    print("del modelo "+modelo+" del escenario "+escenario+", para el año "+str(anyobuscado)+",")
    print("para la zona de "+nombrezona) 

    # Inicia la búsqueda como tal en el listado de archivos disponibles generados
    # en la consulta a la página web. Para cada uno de estos archivos...
    for file in files:

        # ...primero se trae el nombre del archivo,
        archivo=file.opendap_url
    
        # luego se obtienen el año inicial y final que tiene el mismo,
        partsarchivo = archivo.split("_")
        fechas00=partsarchivo[(len(partsarchivo)-1)]
        fechas0=fechas00.split(".")
        fechas=fechas0[0].split("-")
        anyoiniarch = fechas[0][:4]
        anyofinarch = fechas[1][:4]
    
        # después se revisa si el año buscado de los datos está en el rango de años del archivo
        if (int(anyofinarch) >= (anyobuscado)) and (int(anyoiniarch) <= (anyobuscado)):
    
            # Si el archivo tiene el año buscado, se muestra la dirección en la que se puede
            # descargar el archivo completo
            #print("URL del archivo que contiene los datos del año buscado:")
            #print(archivo)
        
            # Y como tal se inicia la extracción de los datos para el año buscado y la zona definida
            anyoini=anyobuscado
            ds = xr.open_dataset(archivo)
            tiemposarch=ds.sizes["time"]
            tiempo_arch=0
            for anyo in range(int(anyoiniarch),(int(anyofinarch)+1)):
                if(anyo==anyobuscado):
                    tiempoini=tiempo_arch
                    if(anyo==int(anyofinarch)):
                        tiempofin=tiemposarch
                    else:
                        if((anyo % 4) == 0):
                            tiempofin=tiempo_arch+temporalidad2
                        else:
                            tiempofin=tiempo_arch+temporalidad1
                    da = ds[varclim]
                    da = da.isel(time=slice(tiempoini, tiempofin))
                    da = da.sel(lat=slice(latmin, latmax), lon=slice((lonmin+360), (lonmax+360)))
                
                    archivonetcdf = rutasalidas+"/"+nomarchsalida
                    da.to_netcdf(archivonetcdf)
                
                    # Una vez realizado el proceso de extracción de los datos del año buscado y de la zona definida,
                    # se muestra el nombre del archivo generado
                    print('Se ha generado el archivo "'+str(archivonetcdf)+'" con los datos del año buscado')
                
                if(anyo % 4 == 0 and anyo % 100 == 0 and anyo % 400 == 0):
                    tiempo_arch=tiempo_arch+temporalidad2
                else:
                    tiempo_arch=tiempo_arch+temporalidad1

#----FIN----
