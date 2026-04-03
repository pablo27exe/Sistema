import os
import subprocess
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import psutil
from auth.db import establecer_conexion, devolver_conexion

KEY_FILENAME = "llave.key"

def obtener_unidades_usb():
    """Lista de rutas de unidades usb"""
    unidades = []
    for particion in psutil.disk_partitions():
        if "removable" in particion.opts or particion.fstype in ("FAT32", "exFAT", "vfat", "FAT"):
            unidades.append(particion.mountpoint)
    return unidades

def generar_y_guardar_llave(usb_path: str):
    llave_privada = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    llave_publica = llave_privada.public_key()
    
    # Serializar llave privada
    bytes_privados = llave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serializar llave publica
    bytes_publicos = llave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo    
    )
    
    # Almacenar clave en USB
    ruta_privada = os.path.join(usb_path, KEY_FILENAME)
    with open(ruta_privada, "wb") as f:
        f.write(bytes_privados)
        
    # Ocultar archivo
    try:
        if sys.platform == 'win32':
            subprocess.run(
                ["attrib", "+H", "+S", ruta_privada],
                check=True,
                capture_output=True
            )
    except Exception as e:
        print(f'No se pudo ocultar el archivo: {e}')
    
    return bytes_publicos.decode()

def guardar_clave_en_bd(usuario_id: str, clave_publica: str):
    """Guarda la clave pública en PostgreSQL"""
    conn = None
    try:
        conn = establecer_conexion()
        cursor = conn.cursor()
        
        # Verificar si la columna clave_publica existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuarios' AND column_name = 'clave_publica'
        """)
        
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE usuarios ADD COLUMN clave_publica TEXT")
        
        # Actualizar la clave pública del usuario
        cursor.execute("""
            UPDATE usuarios 
            SET clave_publica = %s 
            WHERE id = %s
        """, (clave_publica, usuario_id))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error guardando clave en BD: {e}")
        if conn:
            conn.rollback()
        return False
    
    finally:
        if conn:
            devolver_conexion(conn)

def registrar_llave_usb(username: str, on_success, on_error, on_usb_encontrado):
    conn = None
    try:
        unidades = obtener_unidades_usb()
        
        if not unidades:
            on_error("No se encontró ningún USB conectado")
            return
        
        usb_path = unidades[0]
        
        def confirmar_y_generar():
            try:
                clave_publica = generar_y_guardar_llave(usb_path)
                
                # Buscar el usuario en PostgreSQL
                conn = establecer_conexion()
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario = %s", (username,))
                resultado = cursor.fetchone()
                devolver_conexion(conn)
                conn = None
                
                if resultado:
                    usuario_id = str(resultado[0])
                    if guardar_clave_en_bd(usuario_id, clave_publica):
                        on_success(clave_publica)
                    else:
                        on_error("No se pudo guardar la llave en la base de datos")
                else:
                    on_error(f"No se encontró el usuario {username} en la base de datos")
                
            except PermissionError:
                on_error("Sin permisos para escribir en el USB. Intenta como administrador.")
            except Exception as e:
                on_error(f"Error inesperado: {str(e)}")
        
        on_usb_encontrado(usb_path, confirmar_y_generar)

    except Exception as e:
        on_error(f"Error inesperado: {str(e)}")
    finally:
        if conn:
            devolver_conexion(conn)