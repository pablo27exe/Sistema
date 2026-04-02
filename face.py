import cv2
import numpy as np
import os
import pickle
import time
from datetime import datetime
import threading

# import psycopg2
# from psycopg2.extras import Json


def superponer_imagen(frame, imagen_rgba, x, y, w, h):
    """Superpone un PNG con transparencia sobre el frame en la posición del rostro"""
    imagen_redim = cv2.resize(imagen_rgba, (w, h))
    bgr   = imagen_redim[:, :, :3]
    alpha = imagen_redim[:, :, 3] / 255.0
    region = frame[y:y+h, x:x+w]
    for c in range(3):
        region[:, :, c] = (alpha * bgr[:, :, c] + (1 - alpha) * region[:, :, c])
    frame[y:y+h, x:x+w] = region
    return frame


class SistemaAutenticacionFacial:
    def __init__(self):
        """Constructor de la clase"""
        # ── Carpeta dedicada para datos faciales ──────────────────────
        self.data_dir = "facial_data"
        os.makedirs(self.data_dir, exist_ok=True)  # La crea si no existe

        # Rutas centralizadas
        self.ruta_modelo   = os.path.join(self.data_dir, "modelo_facial_auth.yml")
        self.ruta_ids      = os.path.join(self.data_dir, "ids_faciales.pkl")
        self.ruta_usuarios = os.path.join(self.data_dir, "usuarios_auth.pkl")
        
        self.usuarios = {}  # Este diccionario ahora solo se usa para el modelo facial interno
        self.ids_a_usuarios = {}
        self.detector_rostros = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.reconocedor = cv2.face.LBPHFaceRecognizer_create()
        # No cargamos automáticamente al iniciar, lo haremos bajo demanda
        # self.cargar_usuarios()
        # self.cargar_model_facial()
    
    def cargar_usuarios(self):
        try:
            if os.path.exists(self.ruta_usuarios):
                with open(self.ruta_usuarios, "rb") as f:
                    self.usuarios = pickle.load(f)
            else:
                self.usuarios = {}
        except Exception as e:
            print(f"Error cargando usuarios: {e}")
            self.usuarios = {}
    
    def guardar_usuarios(self):
        try:
            with open(self.ruta_usuarios, "wb") as f:
                pickle.dump(self.usuarios, f)
        except Exception as e:
            print(f"Error guardando usuarios: {e}")
    
    def cargar_model_facial(self):
        """Carga el modelo de reconocimiento facial completo"""
        try:
            if os.path.exists(self.ruta_modelo):
                self.reconocedor.read(self.ruta_modelo)
                print("Modelo facial cargado")
            else:
                print("No hay modelo facial previo")

            if os.path.exists(self.ruta_ids):
                with open(self.ruta_ids, "rb") as f:
                    self.ids_a_usuarios = pickle.load(f)
                print(f"{len(self.ids_a_usuarios)} IDs faciales cargados")
            else:
                print("No hay IDs faciales registrados")
                self.ids_a_usuarios = {}

        except Exception as e:
            print(f"No se pudo cargar modelo facial: {e}")
            self.ids_a_usuarios = {}
    
    def cargar_modelo_por_usuario(self, usuario_id):
        """
        Carga SOLO el modelo facial de un usuario específico
        (Para cuando tengas BD, aquí cargarías desde PostgreSQL)
        """
        # Por ahora, cargamos todo el modelo y filtramos
        self.cargar_model_facial()
        
        # Verificar si el usuario existe en el modelo
        if any(v["uuid"] == usuario_id for v in self.ids_a_usuarios.values()):
            print(f"Modelo cargado para usuario ID: {usuario_id}")
            return True
        else:
            print(f"Usuario ID {usuario_id} no tiene modelo facial")
            return False
    
    def guardar_modelo_facial(self):
        """Guarda el modelo facial completo"""
        try:
            self.reconocedor.save(self.ruta_modelo)
            with open(self.ruta_ids, "wb") as f:
                pickle.dump(self.ids_a_usuarios, f)
            print("Modelo facial guardado")
            return True
        except Exception as e:
            print(f"Error guardando modelo facial: {e}")
            return False
    
    def guardar_modelo_usuario(self, usuario_id, nombre_usuario):
        """
        Versión simplificada - solo guarda el modelo actual
        que ya contiene al usuario específico
        """
        return self.guardar_modelo_facial()
    
    def capturar_rostro_auto(self, usuario_id, nombre_usuario):
        """
        Versión automática para ser llamada desde Flet
        No pide datos, solo ejecuta la captura
        Retorna: (success, mensaje)
        """
        print(f"Iniciando captura automática para: {nombre_usuario} (ID: {usuario_id})")
        
        # Verificar cámara
        camara = cv2.VideoCapture(0)
        if not camara.isOpened():
            return False, "No se puede acceder a la cámara"
            
        camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        icono_marco = cv2.imread("cv_resources/marco_rostro.png", cv2.IMREAD_UNCHANGED)
        
        rostros = []
        capturas = 0
        capturas_requeridas = 30
        ventana_nombre = f"Registro Facial - {nombre_usuario}"
        
        while capturas < capturas_requeridas:
            ret, frame = camara.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            rostros_detectados = self.detector_rostros.detectMultiScale(
                gris,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100)
            )
            
            frame_mostrar = frame.copy()
            
            # Dibujo de detecciones
            for (x, y, w, h) in rostros_detectados:
                if icono_marco is not None:
                    frame_mostrar = superponer_imagen(frame_mostrar, icono_marco, x, y, w, h)
                else:
                    cv2.rectangle(frame_mostrar, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Mostrar contador
            cv2.putText(frame_mostrar, f"Capturas: {capturas}/{capturas_requeridas}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
            # Capturar si hay exactamente un rostro
            if len(rostros_detectados) == 1:
                x, y, w, h = rostros_detectados[0]
                region_rostro = gris[y:y+h, x:x+w]
                rostro_redim = cv2.resize(region_rostro, (200, 200))
                rostros.append(rostro_redim)
                capturas += 1
                print(f"Captura {capturas}/{capturas_requeridas}")
                time.sleep(0.3)
            
            cv2.imshow(ventana_nombre, frame_mostrar)
            cv2.setWindowProperty(ventana_nombre, cv2.WND_PROP_TOPMOST, 1)       
            
            # Control de teclas
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                camara.release()
                cv2.destroyAllWindows()
                return False, "Captura cancelada por el usuario"
        
        camara.release()
        cv2.destroyAllWindows()
        
        if len(rostros) >= 20:
            print(f"Se capturaron {len(rostros)} imágenes")
            return self.entrenar_modelo_usuario(rostros, usuario_id, nombre_usuario)
        else:
            return False, f"No hay suficientes capturas ({len(rostros)}/20)"
    
    def entrenar_modelo_usuario(self, rostros, usuario_id, nombre_usuario):
        try:
            if usuario_id not in [v["uuid"] for v in self.ids_a_usuarios.values()]:
                label_int = len(self.ids_a_usuarios)
                self.ids_a_usuarios[label_int] = {
                    "uuid": usuario_id,
                    "nombre": nombre_usuario
                }
            else:
                label_int = next(
                    k for k, v in self.ids_a_usuarios.items()
                    if v["uuid"] == usuario_id
                )

            rostros_arreglo = np.array(rostros, dtype=np.uint8)
            ids_arreglo     = np.full(len(rostros), label_int, dtype=np.int32)

            if os.path.exists(self.ruta_modelo):  # ← ruta centralizada
                print("Actualizando modelo existente")
                self.reconocedor.read(self.ruta_modelo)
                self.reconocedor.update(rostros_arreglo, ids_arreglo)
            else:
                print("Creando nuevo modelo")
                self.reconocedor.train(rostros_arreglo, ids_arreglo)

            if self.guardar_modelo_facial():
                return True, f"Modelo entrenado exitosamente para {nombre_usuario}"
            else:
                return False, "Error guardando el modelo facial"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error: {str(e)}"
        
    def verificar_rostro_auto(self, usuario_id, nombre_usuario,
                           tiempo_espera=30,
                           camara_precalentada=None):
        """
        Versión automática de verificación facial.
        Retorna: (verificado, confianza, mensaje)
        """
        print(f"\nVerificando identidad para: {nombre_usuario} (ID: {usuario_id})")

        # ── Cargar modelo ────────────────────────────────────────────────────
        if not self.ids_a_usuarios:
            if not self.cargar_modelo_por_usuario(usuario_id):
                return False, 0, "No hay modelo facial para este usuario"

        # Buscar label antes del loop para no repetirlo en cada frame
        label_usuario = next(
            (k for k, v in self.ids_a_usuarios.items() if v["uuid"] == usuario_id),
            None
        )

        # ── Obtener cámara ───────────────────────────────────────────────────
        if camara_precalentada and camara_precalentada.lista:
            camara = camara_precalentada.camara
            print("Usando cámara precalentada.")
            # Limpiar buffer acumulado
            for _ in range(5):
                camara.read()
        else:
            print("Abriendo cámara nueva.")
            camara = cv2.VideoCapture(0)
            if not camara.isOpened():
                return False, 0, "No se puede acceder a la cámara"
            camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camara_precalentada = None  # Para no liberar la externa en finally

        icono_marco     = cv2.imread("cv_resources/marco_rostro.png", cv2.IMREAD_UNCHANGED)
        tiempo_inicio   = time.time()
        verificado      = False
        mejor_confianza = 100

        try:
            while time.time() - tiempo_inicio < tiempo_espera and not verificado:
                ret, frame = camara.read()
                if not ret:
                    continue

                frame = cv2.flip(frame, 1)
                gris  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                rostros_detectados = self.detector_rostros.detectMultiScale(
                    gris, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
                )

                frame_mostrar = frame.copy()

                for (x, y, w, h) in rostros_detectados:
                    if icono_marco is not None:
                        frame_mostrar = superponer_imagen(frame_mostrar, icono_marco, x, y, w, h)
                    else:
                        cv2.rectangle(frame_mostrar, (x, y), (x+w, y+h), (0, 255, 0), 2)

                    region_rostro = gris[y:y+h, x:x+w]
                    rostro_redim  = cv2.resize(region_rostro, (200, 200))

                    id_predicho, confianza = self.reconocedor.predict(rostro_redim)

                    if confianza < mejor_confianza:
                        mejor_confianza = confianza

                    nombre_predicho = self.ids_a_usuarios.get(id_predicho, {}).get("nombre", "Desconocido")
                    cv2.putText(frame_mostrar,
                                f"{nombre_predicho} ({100 - confianza:.1f}%)",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                    if id_predicho == label_usuario and confianza < 80:
                        verificado = True
                        cv2.putText(frame_mostrar, "VERIFICADO",
                                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                tiempo_restante = int(tiempo_espera - (time.time() - tiempo_inicio))
                cv2.putText(frame_mostrar, f"Tiempo: {tiempo_restante}s",
                            (10, frame.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                cv2.imshow("Verificacion Facial", frame_mostrar)
                cv2.setWindowProperty("Verificacion Facial", cv2.WND_PROP_TOPMOST, 1)

                if cv2.waitKey(1) & 0xFF == 27:
                    return False, mejor_confianza, "Verificación cancelada"

        finally:
            cv2.destroyAllWindows()
            # Solo liberar si fue abierta localmente
            if camara_precalentada is None:
                camara.release()
            else:
                camara_precalentada.liberar()

        if verificado:
            return True, mejor_confianza, "Verificación exitosa"
        elif mejor_confianza < 100:
            return False, mejor_confianza, f"No se pudo verificar (mejor confianza: {mejor_confianza})"
        else:
            return False, mejor_confianza, "No se detectó ningún rostro"
    

def verificar_instalacion():
    """Verificar que todo esté instalado CV2 y numpy"""
    print("Iniciando proceso de verificación")
    
    try:
        print(f"OpenCV {cv2.__version__}")
        
        try:
            test = cv2.face
            print("Módulo face disponible")
        except AttributeError: 
            print("Módulo cv2.face NO disponible, para solucionarlo:")
            print("pip uninstall opencv-python opencv-contrib-python -y")
            print("pip install opencv-contrib-python==4.10.0.84")
            return False

        print(f"NumPy {np.__version__}")
        return True
    
    except ImportError as e:
        print(f"Error: {e}")
        return False

# Función de prueba para usar desde Flet
def probar_registro_facial(usuario_id, nombre_usuario):
    """
    Función de prueba para llamar desde Flet
    """
    sistema = SistemaAutenticacionFacial()
    return sistema.capturar_rostro_auto(usuario_id, nombre_usuario)

def probar_verificacion_facial(usuario_id, nombre_usuario):
    """
    Función de prueba para verificación
    """
    sistema = SistemaAutenticacionFacial()
    return sistema.verificar_rostro_auto(usuario_id, nombre_usuario)

if __name__ == "__main__":
    # Solo para pruebas directas
    print("Modo de prueba - Simulando llamado desde Flet")
    usuario_prueba_id = 1
    nombre_prueba = "Usuario Prueba"
    
    print("\n1. Probando registro facial...")
    success, msg = probar_registro_facial(usuario_prueba_id, nombre_prueba)
    print(f"Resultado: {success} - {msg}")
    
    if success:
        print("\n2. Probando verificación facial...")
        verificado, confianza, msg = probar_verificacion_facial(usuario_prueba_id, nombre_prueba)
        print(f"Resultado: {verificado} - Confianza: {confianza} - {msg}")