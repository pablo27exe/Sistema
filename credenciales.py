import bcrypt
from db import obtener_conexion, liberar_conexion

def hash_contrasena(contrasena: str) -> str:
    """convierte la contraseña en un hash de bcrypt"""
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

def insertar_credencial(usuario_id: str, contrasena: str):
    """guarda el hash de la conseña asociado al usuario.
    retorna true si la operacion es exitosa, false en caso contrario."""
    conn = None
    try:
        hash = hash_contrasena(contrasena)
        conn = obtener_conexion()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO credenciales (usuario_id, hash_contrasena)
                VALUES (%s, %s)
            """, (usuario_id, hash_contrasena))
        conn.commit() #commit para guardar los cambios en la base de datos
        print(f'Credencial insertada para usuario: {usuario_id}')
        return True

    except Exception as e:
        if conn:
            conn.rollback() #rollback para deshacer los cambios en caso de error
        print(f'Error al insertar la credencial: {e}')
        return False

    finally:
        liberar_conexion(conn) #liberar la conexion a la base de datos