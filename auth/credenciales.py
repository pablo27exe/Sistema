import bcrypt
from psycopg2.extensions import cursor
from .db import establecer_conexion, devolver_conexion

def hash_contrasena(contrasena: str) -> str:
    """convierte la contraseña en un hash de bcrypt"""
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

def insertar_credencial(usuario_id: str, contrasena: str):
    """guarda el hash de la conseña asociado al usuario.
    retorna true si la operacion es exitosa, false en caso contrario."""
    conn = None
    try:
        hash_generado = hash_contrasena(contrasena)
        conn = establecer_conexion()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO credenciales (usuario_id, hash_contrasena)
                VALUES (%s, %s)
            """, (usuario_id, hash_generado))
        conn.commit() #commit para guardar los cambios en la base de datos
        print(f'Credencial insertada para usuario: {usuario_id}')
        return True

    except Exception as e:
        if conn:
            conn.rollback() #rollback para deshacer los cambios en caso de error
        print(f'Error al insertar la credencial: {e}')
        return False

    finally:
        devolver_conexion (conn) #liberar la conexion a la base de datos 
        
def verificar_contrasena(usuario_id: str, contrasena: str) -> bool:
    """
    Compara la contraseña ingresada con el hash que se guardó en la base de datos
    """
    conn = None
    try:
        conn = establecer_conexion()
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT hash_contrasena
                        FROM credenciales
                        WHERE usuario_id = %s
                        """, (usuario_id,))
            resultado = cur.fetchone()

        if not resultado:
            return False
        
        hash_guardado = resultado[0]
        return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())
    
    except Exception as e:
        print(f'Error verificando la contraseña: {e}')
        return False
    finally:
        devolver_conexion(conn)
        