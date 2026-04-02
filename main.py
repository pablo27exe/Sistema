import flet as ft
import threading
import time 
import re
import os

#importar los modulos de los scripts
from qro import enviar_qr_por_bluetooth
from face import SistemaAutenticacionFacial
from usb import registrar_llave_usb, obtener_unidades_usb
from inicio import mostrar_bienvenida
from camara_compartida import CamaraCompartida


#modulos de la base de datos
from usuarios import insertar_usuario, obtener_usuario_por_usuario, eliminar_usuario
from credenciales import insertar_credencial, verificar_contrasena
from segundo_metodo import insertar_metodo, obtener_metodo_por_usuario

#auntenticacion
from autenticacion import iniciar_segundo_factor

def main(page: ft.Page):
    page.title = "Sistema de Autenticación"
    page.padding = 0
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.window.maximized = True
    page.window_width = 800
    page.window_height = 600
    
    dialogo_actual = None
    usuario_actual = None
            
    #variable global para simular usuarios
    next_user_id = 1
    usuarios_registrados = {}
    
    camara_facial = CamaraCompartida()
    camara_qr     = camara_facial
    camara_facial.iniciar()
        
    
     # ── Diálogo que aparece si la cámara aún no está lista ───────────────
    def verificar_camara_lista(camara, on_lista):
        """
        Verifica si la cámara está lista.
        Si no, muestra un diálogo de espera y reintenta.
        """
        if camara.lista:
            on_lista()
            return

        # Mostrar diálogo de espera
        progress = ft.ProgressRing(width=30, height=30, stroke_width=3)
        dialog_espera = ft.AlertDialog(
            title=ft.Text("Preparando cámara", color=ft.Colors.BLUE),
            content=ft.Column([
                ft.Text("La cámara se está iniciando, espere un momento...", size=13),
                ft.Row([progress], alignment="center")
            ], tight=True, spacing=15),
            actions=[]
        )
        page.overlay.append(dialog_espera)
        dialog_espera.open = True
        page.update()

        def esperar_y_continuar():
            lista = camara.esperar_lista(timeout=8)
            def continuar():
                dialog_espera.open = False
                page.update()
                if lista:
                    on_lista()
                else:
                    crear_dialogo(
                        "Error",
                        f"No se pudo acceder a la cámara: {camara.error}",
                        "error"
                    )
            page.run_thread(continuar)

        threading.Thread(target=esperar_y_continuar, daemon=True).start()
    
    
    # ===== FUNCIONES AUXILIARES =====
    def mostrar_pantalla(contenido):
        page.clean()
        page.add(
            ft.Stack(
                controls=[
                    # Capa 1: fondo degradado
                    ft.Container(
                        expand=True,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(0, -1),
                            end=ft.Alignment(0, 1),
                            # ==================== TONOS AZULES ALTERNATIVOS ====================
                            # Azules más vibrantes
                            # colors = ["#0a2f6c", "#1e4a8a", "#2c6e9e"]

                            # Azules turquesa
                            # colors = ["#0c4e6e", "#1b6b8f", "#2a8eb3"]

                            # Azules nocturnos profundos
                            # colors = ["#03045e", "#023e8a", "#0077b6"]


                            # ==================== TONOS CÁLIDOS ====================
                            # Atardecer
                            # colors = ["#ff6b6b", "#f9a26c", "#ffd93d"]

                            # Terracota
                            # colors = ["#9e2a2b", "#e09d32", "#f5e6d3"]

                            # Rosados
                            # colors = ["#d4a5a5", "#e9c7c7", "#ffe6e6"]


                            # ==================== TONOS VERDES ====================
                            # Bosque
                            # colors = ["#1a4d3e", "#2d6a4f", "#40916c"]

                            # Menta
                            # colors = ["#74c69d", "#95d5b2", "#b7e4c7"]

                            # Esmeralda
                            # colors = ["#006d77", "#2a9d8f", "#52b788"]


                            # ==================== TONOS PÚRPURA ====================
                            # Lavanda
                            #colors = ["#6c5b7b", "#8e7d9e", "#b0a1c1"]

                            # Morado neón
                            # colors = ["#7b2cbf", "#9d4edd", "#c77dff"]

                            # Malva
                            # colors = ["#5e4b56", "#806b75", "#a28b95"]


                            # ==================== GRADIENTES CONTRASTE ====================
                            # Noche a día
                            # colors = ["#1e1e2f", "#4a4e6b", "#8a9bb5"]

                            # Puesta de sol marina
                            #colors = ["#0f2027", "#203a43", "#2c5364"]

                            # Rosa a azul
                            colors = ["#ff9a9e", "#fad0c4", "#a1c4fd"]


                            # ==================== GRADIENTES MONOCROMÁTICOS ====================
                            # Gris elegante
                            # colors = ["#2d3436", "#3b4448", "#4b5a5f"]

                            # Beige cálido
                            # colors = ["#e3d9ca", "#d9ceb8", "#cfc3a6"]

                            # Coral
                            # colors = ["#ff7e5e", "#ff8f6e", "#ffa07e"]
                        )
                    ),
                    # Capa 2: contenedor centrado dinámicamente
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Container(
                            content=contenido,
                            width=460,
                            height=660,
                        )
                    )
                ],
                expand=True
            )
        )
        page.update()


    def cerrar_dialogo(dialog): #permite que al dar clic en el botón de aceptar de cada cuadro de dialogo se pueda cerrar
        if dialog:  # Verificar que exista
            dialog.open = False
            page.update()
    
    def crear_dialogo(titulo, mensaje, tipo="info"): #diseñar el estilo del cuadro de dialogo
        """Crea un diálogo estandarizado"""
        
        nonlocal dialogo_actual
        colores = {  #cuando se trata de cierto tipo de mensaje en el dialogo mostrará un color diferente para indicar de que tipo se trata
            "error": ft.Colors.RED,
            "exito": ft.Colors.GREEN,
            "info": ft.Colors.BLUE
        }
        dialog = ft.AlertDialog( #Se crea el dialogo             
            title=ft.Text(titulo, color=colores.get(tipo, ft.Colors.BLACK)), #El titulo será con base a una variable llamda titulo que se usa cuando se manda a llamar el cuadro de dialogo en diferentes partes
            content=ft.Text(mensaje), #El contenido se almacena en una variable llamada mensaje la cual mostrará la información del cuadro de dialogo
            actions=[
                ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog)), #permite incorporar un boton que manda a llamar la funcion de cerrar el dialogo
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dialogo_actual = dialog
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
        return dialog
    
    def crear_dialogo_con_imagen(icono,titulo, mensaje, tipo="info", on_iniciar=None): #diseñar el estilo del cuadro de dialogo
        """Crea un diálogo estandarizado"""
        
        nonlocal dialogo_actual
        colores = {  #cuando se trata de cierto tipo de mensaje en el dialogo mostrará un color diferente para indicar de que tipo se trata
            "error": ft.Colors.RED,
            "exito": ft.Colors.GREEN,
            "info": ft.Colors.BLUE
        }
        
        def inicio(e):
            cerrar_dialogo(dialog)
            if on_iniciar:
                on_iniciar()
                
        acciones = [ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialog))]
        if on_iniciar:
          acciones.insert(0, ft.TextButton("Iniciar", on_click=inicio))    
             
        dialog = ft.AlertDialog( #Se crea el dialogo
            icon=ft.Image(src=icono,width=60, height=60),      
            title=ft.Text(titulo, color=colores.get(tipo, ft.Colors.BLACK)), #El titulo será con base a una variable llamda titulo que se usa cuando se manda a llamar el cuadro de dialogo en diferentes partes
            content=ft.Text(mensaje), #El contenido se almacena en una variable llamada mensaje la cual mostrará la información del cuadro de dialogo
            actions=acciones,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dialogo_actual = dialog
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
        return dialog
    
    def crear_dialogo_automatico(titulo, mensaje, tipo="info", duracion = 2): #diseñar el estilo del cuadro de dialogo
        """Crea un diálogo estandarizado"""
        
        nonlocal dialogo_actual
        colores = {  #cuando se trata de cierto tipo de mensaje en el dialogo mostrará un color diferente para indicar de que tipo se trata
            "info": ft.Colors.BLUE
        }
        dialog = ft.AlertDialog( #Se crea el dialogo
            title=ft.Text(titulo, color=colores.get(tipo, ft.Colors.BLACK)), #El titulo será con base a una variable llamda titulo que se usa cuando se manda a llamar el cuadro de dialogo en diferentes partes
            content=ft.Text(mensaje), #El contenido se almacena en una variable llamada mensaje la cual mostrará la información del cuadro de dialogo
            actions=[],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dialogo_actual = dialog
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
        
        def cerrar_dialogo_automatico():
            time.sleep(duracion)
            page.run_thread(lambda: cerrar_dialogo(dialog))
            
        hilo_cierre = threading.Thread(target=cerrar_dialogo_automatico, daemon=True)
        hilo_cierre.start()
        return dialog
               
    def crear_boton_verificacion(texto, icono, color_fondo, on_click):
        """Crea un botón estandarizado para verificación"""
        return ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Image(src=icono, width=60, height=60),
                    ft.Text(texto, size=17, weight="bold"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            width=300, 
            height=100, 
            bgcolor=color_fondo,
            on_click=on_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=5),
            ),
        )
    
    def crear_container_formulario(titulo, elementos):
        """Crea un container estandarizado para formularios"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(titulo, size=30, weight="bold"),
                    *elementos,  
                ],
                horizontal_alignment="center",
                spacing=10 #if "REGISTRO" in titulo else 15,
            ),
            padding=30,
            bgcolor="white",
            border_radius=50,
            width=400,
        )
    
    # ===== FUNCIONES DE VERIFICACIÓN =====
            
    # ===== PÁGINA 3: VERIFICACIÓN =====
    def mostrar_verificacion(usuario_data):
        nonlocal usuario_actual
        usuario_actual = usuario_data
        #print(f"Usuario actual establecido: {usuario_actual}")

        # Estado compartido
        metodo_elegido = {"valor": False}
        def confirmar_volver_inicio(_):
            def on_confirmar():
                cerrar_dialogo(dialog_confirmacion)
                #eliminar usuario si aun no completó el registro
                if not metodo_elegido["valor"]:
                    eliminar_usuario(usuario_data['id'])
                mostrar_login()
                
            def on_cancelar():
                cerrar_dialogo(dialog_confirmacion)
                
            dialog_confirmacion = ft.AlertDialog(
                title=ft.Text('¿Volver a inicio?'),
                content=ft.Text(
                    "Si vuelves al inicio, tu registro será cancelado y tus datos serán eliminados. ¿Deseas continuar?",size=13
                ),
                actions=[
                    ft.TextButton('Cancelar', on_click=lambda e: on_cancelar()),
                    ft.TextButton('Sí',
                                  on_click=lambda e: on_confirmar()),
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            page.overlay.append(dialog_confirmacion)
            dialog_confirmacion.open = True
            page.update()
            

        def deshabilitar_botones():
            btn_qr.disabled     = True
            btn_usb.disabled    = True
            btn_facial.disabled = True
            page.update()

        def metodo_completado(tipo: str, dato_factor: str = None):
            if metodo_elegido["valor"]:
                return

            metodo_elegido["valor"] = True
            deshabilitar_botones()

            bien = insertar_metodo(
                usuario_id  = usuario_data['id'],
                tipo        = tipo,
                dato_factor = dato_factor
            )

            if bien:
                page.run_thread(lambda: mostrar_bienvenida(
                    page,
                    usuario_data,
                    on_cerrar_sesion=lambda: mostrar_login()
                    ))
            else:
                metodo_elegido["valor"] = False
                page.run_thread(lambda: crear_dialogo(
                    "Error",
                    "No se pudo guardar el método. Intenta de nuevo.",
                    "error"
                ))

        def qr_clicked(e):
            if metodo_elegido["valor"]:
                return
            crear_dialogo_automatico("Proceso iniciado", "Iniciando proceso de escaneo QR...", "info")

            def proceso():
                exito, mensaje, contrasena_qr = enviar_qr_por_bluetooth()

                if not exito or not contrasena_qr:
                    page.run_thread(lambda: crear_dialogo("Error", mensaje, "error"))
                    return

                # Pedir confirmación de que el QR fue recibido
                def mostrar_confirmacion():
                    def on_confirmar():
                        cerrar_dialogo(dialog_confirm)
                        metodo_completado(tipo="QR", dato_factor=contrasena_qr)

                    def on_cancelar():
                        cerrar_dialogo(dialog_confirm)
                        crear_dialogo(
                            "Cancelado",
                            "El registro del QR fue cancelado.",
                            "info"
                        )

                    dialog_confirm = ft.AlertDialog(
                        title=ft.Text("¿Recibiste el QR?", color=ft.Colors.BLUE),
                        content=ft.Text(
                            "Confirma que el código QR fue recibido correctamente en tu teléfono.",
                            size=13
                        ),
                        actions=[
                            ft.TextButton("No recibí", on_click=lambda e: on_cancelar()),
                            ft.TextButton(
                                "Sí, lo recibí",
                                on_click=lambda e: on_confirmar(),
                                style=ft.ButtonStyle(color=ft.Colors.GREEN)
                            ),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END
                    )
                    page.overlay.append(dialog_confirm)
                    dialog_confirm.open = True
                    page.update()

                page.run_thread(mostrar_confirmacion)

            threading.Thread(target=proceso, daemon=True).start()
            

        def llave_clicked(e):
            if metodo_elegido["valor"]:
                return

            datos_usuario = usuario_actual.copy()
            crear_dialogo_automatico("Proceso iniciado", "Iniciando proceso de verificación por llave...", "info", duracion=2)

            def on_usb_encontrado(usb_path, confirmar_y_generar):
                def mostrar_confirmacion():
                    crear_dialogo_con_imagen(
                        "USB.ico",
                        "USB detectado",
                        f"Se generará la llave en: {usb_path}\nPresiona Iniciar para continuar.",
                        "info",
                        on_iniciar=confirmar_y_generar
                    )
                page.run_thread(mostrar_confirmacion)

            def on_success(clave_publica: str):
                metodo_completado(tipo="USB", dato_factor=clave_publica)

            def on_error(mensaje):
                page.run_thread(lambda: crear_dialogo("Error", mensaje, "error"))

            def ejecutar():
                time.sleep(2.2)
                registrar_llave_usb(datos_usuario['username'], on_success, on_error, on_usb_encontrado)

            threading.Thread(target=ejecutar, daemon=True).start()
            

        def facial_clicked(e):
            if metodo_elegido["valor"]:
                return

            datos_usuario = usuario_actual.copy()
            crear_dialogo_automatico("Proceso iniciado", "Iniciando proceso de reconocimiento facial...", "info", duracion=2)

            def mostrar_segundo_dialogo():
                time.sleep(2.2)

                def on_iniciar_facial():
                    def iniciar():
                        sistema_facial = SistemaAutenticacionFacial()
                        def proceso_captura():
                            try:
                                success, dato_facial = sistema_facial.capturar_rostro_auto(
                                    usuario_id     = datos_usuario['id'],
                                    nombre_usuario = datos_usuario['username']
                                )
                                if success:
                                    metodo_completado(tipo="FACIAL", dato_factor=dato_facial)
                                else:
                                    page.run_thread(lambda: crear_dialogo("Error", dato_facial, "error"))
                            except Exception as ex:
                                page.run_thread(lambda: crear_dialogo("Error", str(ex), "error"))
                        threading.Thread(target=proceso_captura, daemon=True).start()

                    verificar_camara_lista(camara_facial, iniciar)
    
                page.run_thread(lambda: crear_dialogo_con_imagen(
                    "FACE.ico",
                    "Instrucciones",
                    "• Colóquese frente a la cámara\n• Asegure buena iluminación\n• Mantenga el rostro centrado\n• La captura será automática",
                    "info",
                    on_iniciar=on_iniciar_facial
                ))

            threading.Thread(target=mostrar_segundo_dialogo, daemon=True).start()

        # ── Botones ─────────────────────────────────────────────────────────────
        btn_qr     = crear_boton_verificacion("Obtener QR",            "QR.ico",   "white", qr_clicked)
        btn_usb    = crear_boton_verificacion("Obtener llave",         "USB.ico",  "white", llave_clicked)
        btn_facial = crear_boton_verificacion("Reconocimiento facial", "FACE.ico", "white", facial_clicked)

        elementos = [
            ft.Text("SEGUNDO MÉTODO DE VERIFICACIÓN", size=24, weight="bold", text_align="center"),
            ft.Text("Elige una opción de verificación:", size=16),
            ft.Container(height=20),
            btn_qr,
            btn_usb,
            btn_facial,
            ft.Container(height=20),
            ft.TextButton(
                content=ft.Text("Volver al inicio"),
                on_click=confirmar_volver_inicio,
            ),
        ]

        verificacion_container = crear_container_formulario("", elementos)
        mostrar_pantalla(verificacion_container) 
    
    # ===== PÁGINA 2: REGISTRO =====
    def registro_exitoso(e):
        # Campos obligatorios
        if not all([usuario.value, nombre.value, password1.value]):
            crear_dialogo("Error", "Todos los campos son obligatorios", "error")
            return
        
        
        #Validar formato: Expresiones regulares para limitar los datos a ingresar
        patron_nombre = patron_nombre = r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]*(?:[\s\-'][A-ZÁÉÍÓÚÑ][a-záéíóúñ]*)*$" #Solo letras a-z, A-Z, guiones, espacios y acentos 
        patron_contrasena = r'^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?]).{8,}$' #Contraseña
        
        if not re.match(patron_nombre, nombre.value.strip()):
            crear_dialogo("Error", "El nombre debe iniciar con mayúscula en cada palabra.","error")
            return
        
            
        if not re.match(patron_contrasena, password1.value.strip()):
            crear_dialogo("Error", "La contraseña debe tener mínimo 8 caracteres, una mayúscula, un número y un carácter especial.","error")
            return
        
        # Coincidencia de contraseñas
        if password1.value != password2.value:
            crear_dialogo("Error", "Las contraseñas no coinciden", "error")
            return

        #Verificar que el usuario ya existe en la base de datos
        if obtener_usuario_por_usuario(usuario.value):
            crear_dialogo("Error", "El usuario ya existe", "error")
            return
        

        # Insertar en la tabla de usuarios (antes, se guardaba en un diccionario con datos del usuario)
        usuario_id = insertar_usuario(
            nombre=nombre.value,
            nombre_usuario=usuario.value
        )

        if not usuario_id:
            crear_dialogo("Error", "No se pudo guardar el usuario", "error")
            return

        # Insertar en la tabla de credenciales
        credencial_insertada = insertar_credencial(
            usuario_id=usuario_id,
            contrasena=password1.value
        )
        if not credencial_insertada:
            crear_dialogo("Error", "Usuario creado, pero no se pudo guardar la credencial", "error")
            return
        
        #flujo normal (aquì va el diccionario)
        usuario_data = {
            'id': usuario_id,
            'username': usuario.value,
            'nombre': nombre.value,
        }
            
        crear_dialogo("Registro exitoso", f"Bienvenido {nombre.value}. Ahora  tu método de verificación.", "exito")
        mostrar_verificacion(usuario_data)

      
    def mostrar_registro(e):       
        global usuario, nombre, password1, password2
        usuario = ft.TextField(label="Usuario", width=300)
        
        nombre = ft.TextField(label="Nombre completo", width=300)
        password1 = ft.TextField(label="Contraseña", password=True, width=300,can_reveal_password=True,)
        password2 = ft.TextField(label="Confirmar contraseña", password=True, width=300,can_reveal_password=True,)
        
        elementos = [
            usuario,
            nombre,
            password1,
            password2,
                ft.ElevatedButton(
                content=ft.Text("Ingresar"),
                width=300,
                on_click=registro_exitoso,
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.DEFAULT: ft.Colors.WHITE,
                        ft.ControlState.HOVERED: ft.Colors.BLACK,
                    },
                    bgcolor={
                        ft.ControlState.DEFAULT: ft.Colors.BLACK,
                        ft.ControlState.HOVERED: ft.Colors.WHITE,
                    },
                    side={
                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK),
                    },
                    elevation={
                        ft.ControlState.DEFAULT: 2,
                        ft.ControlState.HOVERED: 8,
                    },
                    animation_duration=200
                )
            ),
            ft.TextButton(
                content=ft.Text("Volver al inicio"),
                on_click=lambda _: mostrar_login(),
            ),
        ]
        
        registro_container = crear_container_formulario("REGISTRO DE USUARIO", elementos)
        mostrar_pantalla(registro_container) 
    
    # ===== PÁGINA 1: LOGIN =====
    def acceso(e):
        #Validar que el campo no esté vacío
        if not usuario.value:
            crear_dialogo("Error", "Favor de ingresar un usuario", "error")
            return
        
        #Verificar que el usuario esté en la base de datos
        datos_usuario = obtener_usuario_por_usuario(usuario.value.strip())
        if not datos_usuario:
            crear_dialogo("Error", f"El usuario '{usuario.value}' no está registrado.","error")
            return
        
    
        usuario_id = str(datos_usuario[0])
        nombre_display = datos_usuario[1]
        nombre_usuario = datos_usuario[2]
        
        usuario_datos = {
            'id': usuario_id,
            'username': nombre_usuario,
            'nombre': nombre_display
        }
        
        #Detectar el método con el que se registró
        metodo = obtener_metodo_por_usuario(usuario_id)
        #print(f"Metodo retornado: {metodo}")
        if not metodo:
            crear_dialogo("Error", "Este usuario no tiene un método de verificación registrado.","error")
            return
        
        tipo_metodo, dato_factor = metodo
        iniciar_segundo_factor(
            page                     = page,
            datos_usuario            = usuario_datos,
            tipo                     = tipo_metodo,
            dato_factor              = dato_factor,
            crear_dialogo            = crear_dialogo,
            crear_dialogo_con_imagen = crear_dialogo_con_imagen,
            crear_dialogo_automatico = crear_dialogo_automatico,
            cerrar_dialogo           = cerrar_dialogo,
            mostrar_bienvenida       = mostrar_bienvenida,
            mostrar_login            = mostrar_login,
            camara_facial            = camara_facial,
            camara_qr                = camara_qr,
            verificar_camara_lista   = verificar_camara_lista
        )
              
    def mostrar_login():
        if not camara_facial.lista: 
            camara_facial.reiniciar()
        
        global usuario
        usuario = ft.TextField(label="Usuario", width=300)
        
        elementos = [
            usuario,
                ft.ElevatedButton(
                content=ft.Text("Ingresar"),
                width=300,
                on_click=acceso,
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.DEFAULT: ft.Colors.WHITE,
                        ft.ControlState.HOVERED: ft.Colors.BLACK,
                    },
                    bgcolor={
                        ft.ControlState.DEFAULT: ft.Colors.BLACK,
                        ft.ControlState.HOVERED: ft.Colors.WHITE,
                    },
                    side={
                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK),
                    },
                    elevation={
                        ft.ControlState.DEFAULT: 2,
                        ft.ControlState.HOVERED: 8,
                    },
                    animation_duration=200
                )
            ),
            ft.TextButton(
                content=ft.Text("¿No estoy registrado? Regístrate aquí"),
                on_click=mostrar_registro,
            ),
        ]
        
        login_container = crear_container_formulario("INICIAR SESIÓN", elementos)
        mostrar_pantalla(login_container) 
    
    # Iniciar aplicación
    mostrar_login()

ft.app(target=main, assets_dir="assets")