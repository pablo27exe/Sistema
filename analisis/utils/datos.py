# analisis/utils/datos.py
import pandas as pd
import geopandas as gpd
import os

# Rutas relativas al proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DATOS = os.path.join(BASE_DIR, "datos")
RUTA_SHAPEFILES = os.path.join(BASE_DIR, "shapefiles")

def cargar_csv_poblacion():
    """Carga y procesa el CSV de población"""
    
    ruta_csv = os.path.join(RUTA_DATOS, "PoblacionABS.csv")
    
    if not os.path.exists(ruta_csv):
        print(f"❌ No se encontró: {ruta_csv}")
        return None
    
    # Leer CSV
    df = pd.read_csv(ruta_csv, encoding='utf-8-sig', dtype={'CVEGEO': str})
    
    # Limpiar columnas
    df.columns = df.columns.str.replace('ï»¿', '')
    df.columns = df.columns.str.strip()
    
    # Normalizar claves
    df['CVEGEO'] = df['CVEGEO'].astype(str).str.strip().str.zfill(5)
    df['clave_estado'] = df['CVEGEO'].str[:2].str.zfill(2)
    
    # Renombrar columna de población
    if 'POB1' in df.columns:
        df.rename(columns={'POB1': 'poblacion_total'}, inplace=True)
    
    # Agregar nombre de estado
    nombres_estados = {
        '01': 'Aguascalientes', '02': 'Baja California', '03': 'Baja California Sur',
        '04': 'Campeche', '05': 'Coahuila', '06': 'Colima', '07': 'Chiapas',
        '08': 'Chihuahua', '09': 'Ciudad de México', '10': 'Durango', '11': 'Guanajuato',
        '12': 'Guerrero', '13': 'Hidalgo', '14': 'Jalisco', '15': 'México',
        '16': 'Michoacán', '17': 'Morelos', '18': 'Nayarit', '19': 'Nuevo León',
        '20': 'Oaxaca', '21': 'Puebla', '22': 'Querétaro', '23': 'Quintana Roo',
        '24': 'San Luis Potosí', '25': 'Sinaloa', '26': 'Sonora', '27': 'Tabasco',
        '28': 'Tamaulipas', '29': 'Tlaxcala', '30': 'Veracruz', '31': 'Yucatán',
        '32': 'Zacatecas'
    }
    
    df['nombre_estado'] = df['clave_estado'].map(nombres_estados)
    
    return df

def cargar_shapefile_estados():
    """Carga el shapefile de estados"""
    
    # Buscar shapefile nacional
    ruta_nacional = os.path.join(RUTA_SHAPEFILES, "00ent.shp")
    
    if os.path.exists(ruta_nacional):
        return gpd.read_file(ruta_nacional)
    
    # Si no existe, concatenar por estado
    gdf_estados = None
    for carpeta in os.listdir(RUTA_SHAPEFILES):
        ruta_estado = os.path.join(RUTA_SHAPEFILES, carpeta)
        if os.path.isdir(ruta_estado):
            for archivo in os.listdir(ruta_estado):
                if archivo.endswith('_ent.shp'):
                    ruta_shape = os.path.join(ruta_estado, archivo)
                    gdf_temp = gpd.read_file(ruta_shape)
                    if gdf_estados is None:
                        gdf_estados = gdf_temp
                    else:
                        gdf_estados = pd.concat([gdf_estados, gdf_temp], ignore_index=True)
                    break
    
    if gdf_estados is not None:
        gdf_estados['CVEGEO'] = gdf_estados['CVEGEO'].astype(str).str.zfill(2)
    
    return gdf_estados