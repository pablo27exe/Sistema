import flet as ft
import threading
import time 
import re

#importar los modulos de los scripts
from qro import enviar_qr_por_bluetooth
from face import SistemaAutenticacionFacial
from usb import generar_y_guardar_llave, obtener_unidades_usb, registrar_llave_usb

#modulos de la base de datos
from usuarios import insertar_usuario, obtener_usuario_por_usuario
from credenciales import insertar_credencial

def main(page: ft.Page):
    page.title = "Sistema de Autenticación"
    page.padding = 50
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.window_width = 1000
    page.window_height = 1000
    
    dialogo_actual = None
    usuario_actual = None
    
    """Configuración de BD
    DB_CONFIG = {
        'host': 'localhost',
        'data_base': 'bd',
        'user': 'usuario',
        'password': 'contraseña'
        }"""
        
    #variable global para simular usuarios
    next_user_id = 1
    usuarios_registrados = {}
    
    # ===== FUNCIONES AUXILIARES =====
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
    
    def guardar_usuario_local(usuario_data):
        """Versión local sin BD - guarda en diccionario"""
        nonlocal next_user_id
        
        usuario_id = next_user_id
        next_user_id += 1
        
        usuarios_registrados[usuario_id] = {
            'username': usuario_data['username'],
            'nombre': usuario_data['nombre'],
            'password': usuario_data['password'], 
            #'fecha_registro': None  usar datetime.now()
        }
        
        print(f"Usuario guardado localmente: ID {usuario_id} - {usuario_data['username']}")
        return usuario_id
    
    def proceso_segundo_plano():
        try: 
            enviar_qr_por_bluetooth()
            
            def actualizar_interfaz():
                nonlocal dialogo_actual
                if dialogo_actual: 
                    cerrar_dialogo(dialogo_actual) 
                    dialogo_actual = None
                page.update()
            page.run_thread(actualizar_interfaz)
            
        except Exception as e:
            def error_interfaz():
                cerrar_dialogo()
                print(f"Error inesperado: {str(e)}")
                page.update()
            
            page.run_thread(error_interfaz)  
                 
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
    #en versiones futuras permitirá el poder implementar scripts para cada uno de los procesos, por ahora solo muestra un mensaje para indicar que todo va bien
    def qr_clicked(e):
        crear_dialogo_automatico("Proceso iniciado", "Iniciando proceso de escaneo QR...", "info") 
        hilo = threading.Thread(target=proceso_segundo_plano, daemon=True)
        hilo.start()
        
    
    def llave_clicked(e):
        nonlocal usuario_actual
        if usuario_actual is None:
            crear_dialogo("Error", "No hay usuario seleccionado", "error")
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

        def on_success(mensaje):
            page.run_thread(lambda: crear_dialogo("Llave generada", mensaje, "exito"))

        def on_error(mensaje):
            page.run_thread(lambda: crear_dialogo("Error", mensaje, "error"))

        def ejecutar():
            time.sleep(2.2)
            registrar_llave_usb(datos_usuario['username'], on_success, on_error, on_usb_encontrado)

        threading.Thread(target=ejecutar, daemon=True).start()

    # ─── Función para el evento de facial_clicked  (crear_dialogo_con_imagen) ──

    def facial_clicked(e):
        nonlocal usuario_actual
        if usuario_actual is None:
            crear_dialogo("Error", "No hay usuario seleccionado", "error")
            return

        datos_usuario = usuario_actual.copy()
        crear_dialogo_automatico("Proceso iniciado", "Iniciando proceso de reconocimiento facial...", "info", duracion=2)

        def mostrar_segundo_dialogo():
            time.sleep(2.2)

            def on_iniciar_facial():
                sistema_facial = SistemaAutenticacionFacial()
                def proceso_captura():
                    try:
                        success, mensaje = sistema_facial.capturar_rostro_auto(
                            usuario_id=datos_usuario['id'],
                            nombre_usuario=datos_usuario['username']
                        )
                        if success:
                            print("Captura exitosa")
                        else:
                            print(f"Error: {mensaje}")
                    except Exception as ex:
                        print(f"Error: {ex}")

                threading.Thread(target=proceso_captura, daemon=True).start()

            page.run_thread(lambda: crear_dialogo_con_imagen(
                "FACE.ico",
                "Instrucciones",
                "• Colóquese frente a la cámara\n• Asegure buena iluminación\n• Mantenga el rostro centrado\n• La captura será automática",
                "info",
                on_iniciar=on_iniciar_facial
            ))

        threading.Thread(target=mostrar_segundo_dialogo, daemon=True).start()
        
    # ===== PÁGINA 3: VERIFICACIÓN =====
    def mostrar_verificacion(usuario_data):
        nonlocal usuario_actual
        usuario_actual = usuario_data
        print(f"Usuario actual establecido: {usuario_actual}")  # Debug
        page.clean()
        
        botones = [
            crear_boton_verificacion("Obtener QR", "QR.ico", "white", qr_clicked),
            
            crear_boton_verificacion("Obtener llave", "USB.ico", "white", llave_clicked),
            
            crear_boton_verificacion("Reconocimiento facial", "FACE.ico", "white", facial_clicked),
        ]
        
        elementos = [
            ft.Text("SEGUNDO MÉTODO DE VERIFICACIÓN", size=24, weight="bold", text_align="center"),
            ft.Text("Elige una opción de verificación:", size=16),
            ft.Container(height=20),
            *botones,
            ft.Container(height=20),
            ft.TextButton(
                content=ft.Text("Volver al inicio"),
                on_click=lambda _: mostrar_login(),
            ),
        ]
        
        verificacion_container = crear_container_formulario("", elementos)
        page.add(verificacion_container)
        page.update()
    
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
        page.clean()
        
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
                content=ft.Text("Finalizar registro"),
                width=300,
                bgcolor="green",
                on_click=registro_exitoso,
            ),
            ft.TextButton(
                content=ft.Text("Volver al inicio"),
                on_click=lambda _: mostrar_login(),
            ),
        ]
        
        registro_container = crear_container_formulario("REGISTRO DE USUARIO", elementos)
        page.add(registro_container)
        page.update()
    
    # ===== PÁGINA 1: LOGIN =====
    def acceso(e):
        if not usuario.value:
            crear_dialogo("Error", "Favor de ingresar un usuario", "error")
            return
    
    def mostrar_login():
        page.clean()
        
        global usuario
        usuario = ft.TextField(label="Usuario", width=300)
        
        elementos = [
            usuario,
            ft.ElevatedButton(
                content=ft.Text("Ingresar"),
                width=300,
                bgcolor="blue",
                on_click=acceso
            ),
            ft.TextButton(
                content=ft.Text("¿No estoy registrado? Regístrate aquí"),
                on_click=mostrar_registro,
            ),
        ]
        
        login_container = crear_container_formulario("INICIAR SESIÓN", elementos)
        page.add(login_container)
        page.update()
    
    # Iniciar aplicación
    mostrar_login()

ft.app(target=main, assets_dir="assets")