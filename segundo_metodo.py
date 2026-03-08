from typing import final
from db import establecer_conexion, devolver_conexion

def insertar_metodo(usuario_id : str, tipo: str, dato_factor: str = None):
    """
        Guarda el método de segundo factor elegido por el usuario.
        tipo: usb, qr o facial
        dato factor: puede ser la clave púbblica, la ruta del modelo o los datos del qr.
        devuelve true si fue exitoso, false si falla
    """
    conn = None
    try:
        conn = establecer_conexion()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO metodos_segundo_factor (usuario_id, tipo, dato_factor)
                VALUES (%s, %s, %s)
            """, (usuario_id, tipo, dato_factor))
        conn.commit()
        print(f"Método '{tipo}' registrado para usuario_id: {usuario_id}")
        return True
    
    except Exception as e:
        if conn:
            conn.rollback()
        print(f'Error al insertar el método: {e}')
        return False
    
    finally:
        devolver_conexion(conn)
        
def obtener_metodo_por_usuario(usuario_id: str):
    """
    Verfica si el usuario ya tiene un método registrado.
    Retorna el registro o None si no tiene
    """
    conn = None
    try:
        conn = establecer_conexion()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tipo, dato_factor
                FROM metodos_segundo_factor
                WHERE usuario_id = %s AND activo = TRUE
            """, (usuario_id,))
            return cur.fetchone()
        
    except Exception as e:
        print(f'Error al obtener el método: {e}')
        return None

    finally:
        devolver_conexion(conn)