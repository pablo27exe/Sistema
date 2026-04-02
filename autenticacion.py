from nt import error
import os
import threading
import time
import flet as ft
from cryptography.hazmat.primitives import serialization
from usb import obtener_unidades_usb
from credenciales import verificar_contrasena
from leer_qr import leer_qr_camara
from face import SistemaAutenticacionFacial


# autenticacion.py — actualizar la firma de la función
def iniciar_segundo_factor(page, datos_usuario: dict, tipo: str, dato_factor: str,
                            crear_dialogo, crear_dialogo_con_imagen,
                            crear_dialogo_automatico, cerrar_dialogo,
                            mostrar_bienvenida, mostrar_login,
                            camara_facial=None,          # ← agregar
                            camara_qr=None,              # ← agregar
                            verificar_camara_lista=None  # ← agregar
                            ):
    """
    Maneja el flujo completo de autenticación por segundo factor.
    Recibe las funciones de UI como parámetros para no depender de main.
    """

    def autenticacion_exitosa():
        mostrar_bienvenida(
            page,
            datos_usuario,
            on_cerrar_sesion=lambda: mostrar_login()
        )

    def fallback(motivo: str = None):
        if motivo:
            page.run_thread(lambda: crear_dialogo(
                "Método no disponible", motivo, "error"
            ))

        campo_password = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=300
        )
        intentos = {"valor": 0}

        def verificar(e):
            intentos["valor"] += 1
            bien = verificar_contrasena(datos_usuario['id'], campo_password.value)
            if bien:
                cerrar_dialogo(dialog_password)
                autenticacion_exitosa()
            else:
                restantes = 3 - intentos["valor"]
                if restantes <= 0:
                    cerrar_dialogo(dialog_password)
                    crear_dialogo("Bloqueado", "Demasiados intentos fallidos.", "error")
                    mostrar_login()
                else:
                    campo_password.value = ""
                    crear_dialogo(
                        "Error",
                        f"Contraseña incorrecta. Intentos restantes: {restantes}",
                        "error"
                    )
                    page.update()

        dialog_password = ft.AlertDialog(
            title=ft.Text("Ingresa tu contraseña", color=ft.Colors.BLUE),
            content=ft.Column([
                ft.Text("Usa tu contraseña como método alternativo.", size=13),
                campo_password
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialog_password)),
                ft.TextButton("Verificar", on_click=verificar)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.overlay.append(dialog_password)
        dialog_password.open = True
        page.update()

    # ── USB ──────────────────────────────────────────────────────────────
    if tipo == "USB":
        crear_dialogo_automatico(
            "Verificación USB",
            "Conecta tu llave USB...",
            "info",
            duracion=2
        )

        def verificar_usb():
            time.sleep(2.2)
            unidades = obtener_unidades_usb()

            if not unidades:
                page.run_thread(lambda: crear_dialogo_con_imagen(
                    "USB.ico",
                    "USB no encontrado",
                    "No se detectó ningún USB. Conecta tu llave o usa tu contraseña.",
                    "error",
                    on_iniciar=lambda: fallback()
                ))
                return

            ruta = None
            for unidad in unidades:
                for nombre in ['llave.key', '.llave.key']:
                    candidato = os.path.join(unidad, nombre)
                    if os.path.exists(candidato):
                        ruta = candidato
                        break
                if ruta:
                    break

            if not ruta:
                page.run_thread(lambda: crear_dialogo_con_imagen(
                    "USB.ico",
                    "Llave no encontrada",
                    "El USB conectado no contiene una llave registrada.",
                    "error",
                    on_iniciar=lambda: fallback()
                ))
                return

            try:
                with open(ruta, "rb") as f:
                    llave_privada = serialization.load_pem_private_key(
                        f.read(), password=None
                    )

                llave_publica = llave_privada.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()

                # ── Diagnóstico temporal ──────────────────────────────
                print(f"Clave pública del USB:\n'{llave_publica}'")
                print(f"Clave pública en BD:\n'{dato_factor}'")
                print(f"Son iguales: {llave_publica.strip() == dato_factor.strip()}")
                # ─────────────────────────────────────────────────────

                if llave_publica.strip() == dato_factor.strip():
                    page.run_thread(autenticacion_exitosa)
                else:
                    page.run_thread(lambda: fallback(
                        "La llave USB no coincide con la registrada."
                    ))

            except Exception as ex:
                page.run_thread(lambda: fallback(
                    f"Error leyendo la llave: {str(ex)}"
                ))

        threading.Thread(target=verificar_usb, daemon=True).start()
    
    #QR    
    elif tipo == 'QR':
        _camara_qr = camara_qr
        
        crear_dialogo_automatico(
            'Verificación QR',
            'Abriendo cámara para leer tu código QR...',
            'info',
            duracion=2
        )
        
        def proceso_qr():
            time.sleep(0.1)
            try:
                print(f"Antes de llamar - _camara_qr: {_camara_qr}")
                print(f"Antes de llamar - lista: {_camara_qr.lista if _camara_qr else 'None'}")
                
                exito, dato_leido = leer_qr_camara(
                    tiempo_espera       = 30,
                    camara_precalentada = _camara_qr
                )
                 
                if not exito:
                     page.run_thread(lambda: fallback(
                         f'No se puede leer el QR: {dato_leido}'
                     ))
                     return
                 
                if dato_leido.strip()  == dato_factor.strip():
                     page.run_thread(autenticacion_exitosa)
                else:
                    page.run_thread(lambda: fallback(
                        'El código QR no coincide con el registrado'
                    ))
                    
            except Exception as e:
                page.run_thread(lambda: fallback(
                    f'Error leyendo QR: {str(e)}'
                ))
                
        threading.Thread(target=proceso_qr, daemon=True).start()

    #FACIAL
    elif tipo == "FACIAL":
        def proceso_facial():
            _camara_facial = camara_facial
            print(f"Estado cámara al iniciar FACIAL: lista={_camara_facial.lista}, error={_camara_facial.error}")
            try:
                sistema = SistemaAutenticacionFacial()
                verificado, confianza, mensaje = sistema.verificar_rostro_auto(
                    usuario_id          = datos_usuario['id'],
                    nombre_usuario      = datos_usuario['username'],
                    camara_precalentada = _camara_facial  # ← pasar aquí
                )
                if verificado:
                    page.run_thread(autenticacion_exitosa)
                else:
                    page.run_thread(lambda: fallback(
                        f"Verificación facial fallida: {mensaje}"
                    ))
            except Exception as ex:
                error_message = str(ex)
                page.run_thread(lambda: fallback(
                    f"Error en reconocimiento facial: {error_message}"
                ))

        crear_dialogo_con_imagen(
            "FACE.ico",
            "Verificación facial",
            "• Colóquese frente a la cámara\n• Asegure buena iluminación\n• Mantenga el rostro centrado",
            "info",
            on_iniciar=lambda: threading.Thread(
                target=proceso_facial, daemon=True
            ).start()
        )
        
    else:
        fallback(f"Método '{tipo}' no reconocido.")