import flet as ft
from qro import enviar_qr_por_bluetooth
import threading

# Aquí va tu código del menú

def main(page: ft.Page):
    page.title = "Sistema de Autenticación"
    page.padding = 50
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    
    dialogo_actual = None
    
    # ===== FUNCIONES AUXILIARES =====
    def cerrar_dialogo(dialog): #permite que al dar clic en el botón de aceptar de cada cuadro de dialogo se pueda cerrar
        if dialog:  # <-- Verificar que exista
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
        crear_dialogo("Proceso iniciado", "Iniciando proceso de escaneo QR...", "info")
        
        hilo = threading.Thread(target=proceso_segundo_plano, daemon=True)
        hilo.start()
        
    
    def llave_clicked(e):
        crear_dialogo("Proceso iniciado", "Iniciando proceso de verificación por llave...", "info")
    
    def facial_clicked(e):
        crear_dialogo("Proceso iniciado", "Iniciando proceso de reconocimiento facial...", "info")
    
    # ===== PÁGINA 3: VERIFICACIÓN =====
    def mostrar_verificacion():
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
        if password1.value != password2.value:
            crear_dialogo("Error", "Las contraseñas no coinciden", "error")
            return
        
        if not all([usuario.value, nombre.value, password1.value]):
            crear_dialogo("Error", "Todos los campos son obligatorios", "error")
            return
        
        crear_dialogo("Registro exitoso", f"Bienvenido {nombre.value}. Ahora  tu método de verificación.", "exito")
        mostrar_verificacion()
    
    def mostrar_registro(e):
        page.clean()
        
        global usuario, nombre, password1, password2
        usuario = ft.TextField(label="Usuario", width=300)
        nombre = ft.TextField(label="Nombre completo", width=300)
        password1 = ft.TextField(label="Contraseña", password=True, width=300)
        password2 = ft.TextField(label="Confirmar contraseña", password=True, width=300)
        
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