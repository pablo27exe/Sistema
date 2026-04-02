import cv2
import time
import threading


class CamaraCompartida:
    """
    Una sola instancia de cámara compartida entre facial y QR.
    Se inicializa al arrancar el programa.
    """
    def __init__(self):
        self.camara  = None
        self.lista   = False
        self.error   = None
        self._lock   = threading.Lock()

    def iniciar(self):
        threading.Thread(target=self._abrir, daemon=True).start()

    def _abrir(self):
        try:
            self.camara = cv2.VideoCapture(0)
            if self.camara.isOpened():
                time.sleep(0.5)
                self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                # Limpiar buffer inicial
                for _ in range(10):
                    self.camara.read()

                self.lista = True
                print("Cámara compartida precalentada y lista.")
            else:
                self.error = "No se puede acceder a la cámara."
        except Exception as ex:
            self.error = str(ex)

    def esperar_lista(self, timeout: int = 8) -> bool:
        inicio = time.time()
        while time.time() - inicio < timeout:
            if self.lista:
                return True
            if self.error:
                return False
            time.sleep(0.1)
        return self.lista

    def liberar(self):
        with self._lock:
            if self.camara:
                self.camara.release()
                self.camara = None
                self.lista  = False
            #Reiniciar automaticamente en background
            threading.Thread(target=self._abrir, daemon=True).start()

    def reiniciar(self):
        """Reinicia la cámara para la siguiente sesión."""
        self.liberar()
        self.error = None
        self.iniciar()