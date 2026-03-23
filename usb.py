
import os
import subprocess
import webbrowser
import sys
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import psutil

"""Base de datos simulada"""
USERS_DB = {}

KEY_FILENAME = "llave.key"
PUB_FILENAME = "llave.pub"

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
    
    #Serializar llave privada
    bytes_privados = llave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    #Serializar llave publica
    bytes_publicos = llave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo    
    )
    
    #Almacenar clave en USB
    
    ruta_privada = os.path.join(usb_path, KEY_FILENAME)
    with open(ruta_privada, "wb") as f:
        f.write(bytes_privados)
        
    #Ocultar archivo
    try:
        if sys.platform == 'win32':
            #Atributo de oculto en windows
            subprocess.run(
                ["attrib","+H","+S",ruta_privada],
                check=True,
                capture_output=True
            )
            #print(f'Archivo ocultado:{ruta_privada}')
    except Exception as e:
        #print(f'No se pudo ocultar el archivo: {e}')
        
        return bytes_publicos.decode() #Devuelve la pública para almacenarla en la DB

#Registro de llave

def registrar_llave_usb(username: str, on_success, on_error, on_usb_encontrado):
    try:
        unidades = obtener_unidades_usb()
        
        if not unidades:
            on_error("No se encontró ningún USB conectado")
            return
        
        usb_path = unidades[0]
        
        def confirmar_y_generar():
            try:
                clave_publica = generar_y_guardar_llave(usb_path)
                
                if username not in USERS_DB:
                    USERS_DB[username] = {}
                USERS_DB[username]["public_key"] = clave_publica
                USERS_DB[username]["tiene_usb"] = True
                
                on_success(clave_publica)
                
                webbrowser.open(usb_path)
                
            except PermissionError:
                on_error("Sin permisos para escribir en el USB. Intenta como administrador.")
            except Exception as e:
                on_error(f"Error inesperado: {str(e)}")
        
        on_usb_encontrado(usb_path, confirmar_y_generar)

    except Exception as e:
        on_error(f"Error inesperado: {str(e)}")