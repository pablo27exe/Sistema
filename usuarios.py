import re
from db import establecer_conexion, devolver_conexion #importar las funciones de la base de datos

def insertar_usuario(nombre: str, nombre_usuario: str):
    """Inserta un nuevo usuario en la base de datos en la tabla usuarios.
    retorna el UUID del usuario o None en caso de error."""
    conn = None #inicializar la conexion a la base de datos
    try:
        conn = establecer_conexion() #obtener la conexion a la base de datos
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO usuarios (nombre, nombre_usuario)
                VALUES (%s, %s)
                RETURNING id
                """,(nombre, nombre_usuario))
            usuario_id = cur.fetchone()[0] #retornar el UUID del usuario
            conn.commit() #commit para guardar los cambios en la base de datos
            print(f'Usuario insertado: {nombre_usuario} con ID: {usuario_id}')
            return str(usuario_id)

    except Exception as e:
        if conn:
            conn.rollback() #rollback para deshacer los cambios en caso de error
        print(f'Error al insertar el usuario: {e}')
        return None

    finally:
        devolver_conexion(conn) #liberar la conexion a la base de datos

def obtener_usuario_por_usuario(nombre_usuario: str):
    """Obtiene un usuario por su nombre de usuario."""
    conn = None
    try:
        conn = establecer_conexion()
        with conn.cursor() as cur:
            cur.execute("""
            SELECT id, nombre, nombre_usuario, fecha_creacion
            FROM usuarios
            WHERE nombre_usuario = %s
            """,(nombre_usuario,))
            return cur.fetchone()

    except Exception as e:
        print(f'Error al obtener el usuario: {e}')
        return None

    finally:
        devolver_conexion(conn) #liberar la conexion a la base de datos
        
    
def eliminar_usuario(usuario_id: str) -> bool:
    """
    Eliminar un usuario y sus datos relacionados (CASCADE en BD).
    Retorna True si fue exitoso, False si falló
    """
    
    conn = None
    try:
        conn = establecer_conexion()
        with conn.cursor() as cur:
            cur.execute("""
                        DELETE FROM usuarios
                        WERE id = %s
                        """, (usuario_id))
        conn.commit()
        print(f'Usuario {usuario_id} eliminado correctamente.')
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f'Error al eliminar usuario: {e}')
        return False
    finally:
        devolver_conexion(conn)