import os
import random
import subprocess
import tempfile
import threading
import time
import qrcode


# ── Configuración de rutas ──────────────────────────────────────────────────
CARPETA_TEMP = tempfile.gettempdir()


# ── Generador de contraseña ─────────────────────────────────────────────────
class GeneradorContrasena:
    CARACTERES = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!#$@&"

    def __init__(self, longitud: int = 10):
        self.longitud = longitud

    def generar(self) -> str:
        return "".join(random.choice(self.CARACTERES) for _ in range(self.longitud))


# ── Generador de QR ─────────────────────────────────────────────────────────
class GeneradorQR:
    def __init__(self, version: int = 10, box_size: int = 10, border: int = 4):
        self.version = version
        self.box_size = box_size
        self.border = border

    def generar_y_guardar(self, datos: str, ruta: str) -> None:
        """Genera el QR con los datos indicados y lo guarda en la ruta dada."""
        qr = qrcode.QRCode(
            version=self.version,
            box_size=self.box_size,
            border=self.border,
        )
        qr.add_data(datos)
        qr.make(fit=True)
        imagen = qr.make_image(fill_color="black", back_color="white")
        imagen.save(ruta)
        print(f"QR guardado en: {ruta}")


# ── Eliminación diferida del archivo temporal ───────────────────────────────
def _eliminar_tras_espera(ruta: str, segundos: int = 30) -> None:
    """Elimina el archivo de imagen después de segundos para dar tiempo a la transferencia."""
    def _tarea():
        time.sleep(segundos)
        try:
            os.remove(ruta)
            print(f"Archivo temporal eliminado: {ruta}")
        except OSError:
            pass

    threading.Thread(target=_tarea, daemon=True).start()


# ── Bluetooth ───────────────────────────────────────────────────────────────
def enviar_por_bluetooth(ruta_archivo: str) -> tuple[bool, str]:
    """
    Intenta enviar el archivo usando fsquirt (herramienta nativa de Windows).
    Si falla, abre el Explorador con el archivo seleccionado para envío manual.
    Retorna (exito, mensaje).
    """
    if not os.path.exists(ruta_archivo):
        return False, f"Archivo no encontrado: {ruta_archivo}"

    ruta_completa = os.path.abspath(ruta_archivo)

    # Intentar con asistente nativo de Bluetooth
    resultado = subprocess.run(
        f'fsquirt -send "{ruta_completa}"',
        shell=True,
        capture_output=True,
    )
    if resultado.returncode == 0:
        print("Asistente de Bluetooth abierto correctamente.")
        return True, "Asistente de Bluetooth abierto"

    # Fallback: abrir carpeta con el archivo seleccionado
    print("fsquirt no disponible — abriendo carpeta para envío manual.")
    subprocess.run(f'explorer /select,"{ruta_completa}"', shell=True)
    return True, "Archivo listo para compartir manualmente"


# ── Registro de datos (preparado para BD) ───────────────────────────────────
class RegistroContrasena:
    """Almacena los datos generados en memoria hasta integrar la base de datos."""
    def __init__(self):
        self._registros: list[dict] = []

    def guardar(self, contrasena: str) -> dict:
        from datetime import datetime
        registro = {
            "contrasena": contrasena,
            "fecha": datetime.now().isoformat(),
        }
        self._registros.append(registro)
        return registro

    def obtener_todos(self) -> list[dict]:
        return list(self._registros)


# Instancia global lista para usar desde Flet u otros módulos
registro = RegistroContrasena()


# ── Función principal ───────────────────────────────────────────────────────
def enviar_qr_por_bluetooth(longitud: int = 12) -> tuple[bool, str, str | None]:
    """
    Genera una contraseña, crea su QR, lo envía por Bluetooth y guarda los datos.
    Retorna (exito, mensaje, contraseña).
    """
    ruta_qr = os.path.join(CARPETA_TEMP, "qr_temp.png")

    try:
        # 1. Generar contraseña
        contrasena = GeneradorContrasena(longitud=longitud).generar()
        print(f"Contraseña generada: {contrasena}")

        # 2. Generar y guardar QR
        GeneradorQR(version=5, box_size=8).generar_y_guardar(contrasena, ruta_qr)

        # 3. Enviar por Bluetooth
        exito_bt, mensaje_bt = enviar_por_bluetooth(ruta_qr)
        print(f"Bluetooth: {mensaje_bt}")

        # 4. Programar eliminación de la imagen temporal
        _eliminar_tras_espera(ruta_qr, segundos=30)

        # 5. Guardar datos en memoria
        registro.guardar(contrasena)

        # Retorna True siempre que se generó la contraseña,
        # independientemente del resultado del Bluetooth
        return True, mensaje_bt, contrasena

    except Exception as error:
        if os.path.exists(ruta_qr):
            os.remove(ruta_qr)
        return False, f"Error: {error}", None