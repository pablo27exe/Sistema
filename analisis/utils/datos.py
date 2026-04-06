# analisis/utils/datos.py
import pandas as pd
import geopandas as gpd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DATOS = os.path.join(BASE_DIR, "datos")
RUTA_SHAPEFILES = os.path.join(BASE_DIR, "shapefiles")

NOMBRES_ESTADOS = {
    '01': 'Aguascalientes',    '02': 'Baja California',
    '03': 'Baja California Sur','04': 'Campeche',
    '05': 'Coahuila',          '06': 'Colima',
    '07': 'Chiapas',           '08': 'Chihuahua',
    '09': 'Ciudad de México',  '10': 'Durango',
    '11': 'Guanajuato',        '12': 'Guerrero',
    '13': 'Hidalgo',           '14': 'Jalisco',
    '15': 'México',            '16': 'Michoacán',
    '17': 'Morelos',           '18': 'Nayarit',
    '19': 'Nuevo León',        '20': 'Oaxaca',
    '21': 'Puebla',            '22': 'Querétaro',
    '23': 'Quintana Roo',      '24': 'San Luis Potosí',
    '25': 'Sinaloa',           '26': 'Sonora',
    '27': 'Tabasco',           '28': 'Tamaulipas',
    '29': 'Tlaxcala',          '30': 'Veracruz',
    '31': 'Yucatán',           '32': 'Zacatecas'
}


# ── Helper interno ──────────────────────────────────────────────────────────

def _leer_csv(nombre_archivo: str, mapeo: dict) -> pd.DataFrame | None:
    """
    Carga un CSV del SCINCE, normaliza claves geográficas,
    renombra columnas según el mapeo dado y agrega nombre_estado.
    """
    ruta = os.path.join(RUTA_DATOS, nombre_archivo)

    if not os.path.exists(ruta):
        print(f"No se encontró: {ruta}")
        return None

    df = pd.read_csv(ruta, encoding="utf-8-sig", dtype={"CVEGEO": str})

    # Limpiar BOM y espacios en nombres de columna
    df.columns = df.columns.str.replace("ï»¿", "").str.strip()

    # Normalizar clave geoestadística
    df["CVEGEO"]       = df["CVEGEO"].astype(str).str.strip().str.zfill(5)
    df["clave_municipio"] = df["CVEGEO"]
    df["clave_estado"] = df["CVEGEO"].str[:2].str.zfill(2)

    # Renombrar solo las columnas presentes en el mapeo
    cols = {k: v for k, v in mapeo.items() if k in df.columns}
    df.rename(columns=cols, inplace=True)
    print(f"{nombre_archivo}: {len(df)} filas, {len(cols)} columnas renombradas")

    # Nombre de estado derivado de la clave
    df["nombre_estado"] = df["clave_estado"].map(NOMBRES_ESTADOS)

    return df

# ── Población ───────────────────────────────────────────────────────────────

def cargar_csv_poblacion(tipo: str = "abs") -> pd.DataFrame | None:
    """
    tipo: "abs" → PoblacionABS.csv   |   "rel" → PoblacionREL.csv
    """
    from utils.mapeos import MAPEO_POBLACION_ABS, MAPEO_POBLACION_REL, COLUMNAS_GEOGRAFICAS

    archivo = "PoblacionABS.csv" if tipo == "abs" else "PoblacionREL.csv"
    mapeo   = {**COLUMNAS_GEOGRAFICAS,
               **(MAPEO_POBLACION_ABS if tipo == "abs" else MAPEO_POBLACION_REL)}
    return _leer_csv(archivo, mapeo)


# ── Economía ────────────────────────────────────────────────────────────────

def cargar_csv_economicas(tipo: str = "abs") -> pd.DataFrame | None:
    """
    tipo: "abs" → EconomiaABS.csv   |   "rel" → EconomiaREL.csv
    """
    from utils.mapeos import MAPEO_ECONOMICAS_ABS, MAPEO_ECONOMICAS_REL, COLUMNAS_GEOGRAFICAS

    archivo = "EconomiaABS.csv" if tipo == "abs" else "EconomiaREL.csv"
    mapeo   = {**COLUMNAS_GEOGRAFICAS,
               **(MAPEO_ECONOMICAS_ABS if tipo == "abs" else MAPEO_ECONOMICAS_REL)}
    return _leer_csv(archivo, mapeo)


# ── Salud ────────────────────────────────────────────────────────────────────

def cargar_csv_salud(tipo: str = "abs") -> pd.DataFrame | None:
    """
    tipo: "abs" → SaludABS.csv (valores absolutos)
          "rel" → SaludREL.csv (porcentajes)
    """
    from utils.mapeos import MAPEO_SALUD_ABS, MAPEO_SALUD_REL, COLUMNAS_GEOGRAFICAS

    if tipo == "abs":
        archivo = "SaludABS.csv"
        mapeo = {**COLUMNAS_GEOGRAFICAS, **MAPEO_SALUD_ABS}
    else:
        archivo = "SaludREL.csv"
        mapeo = {**COLUMNAS_GEOGRAFICAS, **MAPEO_SALUD_REL}
    
    return _leer_csv(archivo, mapeo)


# ── Shapefiles ───────────────────────────────────────────────────────────────

def cargar_shapefile_estados() -> gpd.GeoDataFrame | None:
    """Carga los shapefiles de estados desde las carpetas individuales"""
    
    partes = []
    for carpeta in sorted(os.listdir(RUTA_SHAPEFILES)):
        ruta_carpeta = os.path.join(RUTA_SHAPEFILES, carpeta)
        if not os.path.isdir(ruta_carpeta):
            continue
        for archivo in os.listdir(ruta_carpeta):
            if archivo.endswith("_ent.shp"):
                partes.append(gpd.read_file(os.path.join(ruta_carpeta, archivo)))
                break

    if not partes:
        print("No se encontraron shapefiles de estados")
        return None

    gdf = pd.concat(partes, ignore_index=True)
    gdf["CVEGEO"] = gdf["CVEGEO"].astype(str).str.zfill(2)
    print(f"Shapefile estados: {len(gdf)} entidades")
    return gdf


def cargar_shapefile_municipios() -> gpd.GeoDataFrame | None:
    """Carga los shapefiles de municipios desde las carpetas individuales"""
    
    partes = []
    for carpeta in sorted(os.listdir(RUTA_SHAPEFILES)):
        ruta_carpeta = os.path.join(RUTA_SHAPEFILES, carpeta)
        if not os.path.isdir(ruta_carpeta):
            continue
        for archivo in os.listdir(ruta_carpeta):
            if archivo.endswith("_mun.shp"):
                partes.append(gpd.read_file(os.path.join(ruta_carpeta, archivo)))
                break

    if not partes:
        print("No se encontraron shapefiles de municipios")
        return None

    gdf = pd.concat(partes, ignore_index=True)
    gdf["CVEGEO"] = gdf["CVEGEO"].astype(str).str.zfill(5)
    print(f"Shapefile municipios: {len(gdf)} municipios")
    return gdf