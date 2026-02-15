import flet as ft

def main(page: ft.Page):
    page.title = "Sistema de Autenticación"
    page.padding = 50
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    
    # ===== FUNCIONES AUXILIARES =====
    def cerrar_dialogo(dialog):
        dialog.open = False
        page.update()
    
    def crear_dialogo(titulo, mensaje, tipo="info"):
        """Crea un diálogo estandarizado"""
        colores = {
            "error": ft.Colors.RED,
            "exito": ft.Colors.GREEN,
            "info": ft.Colors.BLUE
        }
        dialog = ft.AlertDialog(
            title=ft.Text(titulo, color=colores.get(tipo, ft.Colors.BLACK)),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
    
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
                    *elementos,  # Expande la lista de elementos
                ],
                horizontal_alignment="center",
                spacing=10 if "REGISTRO" in titulo else 15,
            ),
            padding=30,
            bgcolor="white",
            border_radius=50,
            width=400,
        )
    
    # ===== FUNCIONES DE VERIFICACIÓN =====
    def qr_clicked(e):
        crear_dialogo("Proceso iniciado", "Iniciando proceso de escaneo QR...", "info")
    
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
        
        crear_dialogo("Registro exitoso", f"Bienvenido {nombre.value}. Ahora elige tu método de verificación.", "exito")
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