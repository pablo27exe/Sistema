import os
import psycopg2 #librería que permite hacer la conexión a Postgres
from psycopg2 import pool #permite reutilizar conexiones de bases de datos
from dotenv import load_dotenv #permite cargar variables de entorno

#cargar las variables de entorno

load_dotenv()

#configuración de la base de datos

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

#--Pool de conexiones--
#minconn: conexiones mínimas que mantienen abiertas aunque no se usen
#maxconn: limite de conexiones simultaneas permitidas

try:
    connection_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        **DB_CONFIG
    )
    print("Pool de conexiones creando correctamente")
    
except psycopg2.OperationalError as e:
    print(f"Error la conectar con la base de datos: {e}")
    connection_pool = None
    
#--Funciones públicas--
def establecer_conexion():
    """Entrega una coneción disponible del pool. La llaman los demás módulos cuando necesitan hacer una consulta"""
    if connection_pool is None:
        raise Exception("No hay conexion disponible con la base de datos")
    
    try:
        return connection_pool.getconn()
    except psycopg2.pool.PoolError as e:
        raise Exception(f"Pool sin conexiones disponibles: {e}")
    
def devolver_conexion(conn):
    """Devuelve la conexion al pool una vez que el modulo termino de usarla. Siempre debe llamarse despues de estabelcer_conexion(), siempre"""
    if connection_pool and conn:
        connection_pool.putconn(conn)
        
def cerrar_pool():
    """Cierra todas las conexiones del pool. Se llama cuando la aplicacion termina"""
    
    if connection_pool:
        connection_pool.closeall()
        print("Pool de conexiones cerrado")