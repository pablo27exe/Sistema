import cv2
import time

def leer_qr_camara(tiempo_espera: int = 25) -> tuple[bool, str]:
    """
    Abre la cámara y espera que el usuario muestre su QR.
    Retorna (exito, dato_leido) o (False, mensaje_error).
    """
    camara = cv2.VideoCapture(0)
    if not camara.isOpened():
        return False, 'No se puede acceder a la cámara.'
    
    camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    detector = cv2.QRCodeDetector()
    tiempo_inicio = time.time()
    
    print('Cámara abierta')
    
    while time.time() - tiempo_inicio < tiempo_espera:
        ret, frame = camara.read()
        if not ret:
            continue
        
        frame = cv2.flip(frame,1)
        
        #Intentar detectar y decodificar el QR
        dato, puntos, _ = detector.detectAndDecode(frame)
        
        #Dibujar el contorno si detectar el QR
        if puntos is not None:
            puntos = puntos.astype(int)
            for i in range(len(puntos[0])):
                pt1 = tuple(puntos[0][i])
                pt2 = tuple(puntos[0][(i + 1) % len(puntos[0])])
                cv2.line(frame, pt1, pt2, (255, 255, 255), 2)
                
        if dato:
            cv2.putText(frame, "QR detectado!", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Verificacion QR", frame)
            cv2.waitKey(800)  # Mostrar un momento antes de cerrar
            camara.release()
            cv2.destroyAllWindows()
            print(f"QR leído: {dato}")
            return True, dato

        cv2.imshow("Verificacion QR", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC para cancelar
            break
        
    camara.release()
    cv2.destroyAllWindows()
    return False, "No se detectó ningún código QR en el tiempo límite."