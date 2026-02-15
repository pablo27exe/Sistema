import flet as ft

def main(page: ft.Page):
    page.title = "Sistema de Autenticación"
    page.padding = 50
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    
    # Función para cerrar diálogo
    def cerrar_dialogo(dialog):
        dialog.open = False
        page.update()
    
    # Función para mostrar ventana emergente
    def mostrar_proceso(mensaje):
        dialog = ft.AlertDialog(
            title=ft.Text("Proceso iniciado"),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
    
    # Función para los botones de verificación
    def qr_clicked(e):
        mostrar_proceso("Iniciando proceso de escaneo QR...")
    
    def llave_clicked(e):
        mostrar_proceso("Iniciando proceso de verificación por llave...")
    
    def facial_clicked(e):
        mostrar_proceso("Iniciando proceso de reconocimiento facial...")
    
    # Página 3: Métodos de verificación
    def mostrar_verificacion():
        page.clean()
        
        verificacion_container = ft.Container(
            content=ft.Column([
                ft.Text("SEGUNDO MÉTODO DE VERIFICACIÓN", size=24, weight="bold",text_align="center"),
                ft.Text("Elige una opción de verificación:", size=16),
                ft.Container(height=20),
                
                # Botón QR
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Image(
                                src="QR.ico", 
                                width=60,
                                height=60,
                            ),
                            ft.Text("Obtener QR", size=17),
                        ],
                        
                    ),
                    width=300, height= 100, bgcolor="white",        
                    on_click=qr_clicked,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        ),
                ),
                ft.Container(height=10),
                
                # Botón Llave
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Image(
                                src="USB.ico", 
                                width=60,
                                height=60,
                            ),
                            ft.Text("Obtener llave", size=17),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10,
                    ),
                    width=300, height= 100, bgcolor="white",   
                    on_click=llave_clicked,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        ),
                ),
                ft.Container(height=10),
                
                # Botón Reconocimiento facial
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Image(
                                src="FACE.ico", 
                                width=60,
                                height=60,
                            ),
                            ft.Text("Reconocimiento facial", size=17),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10,
                    ),
                    width=300, height=100, bgcolor="white",
                    on_click=facial_clicked,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                    ),
                ),
                ft.Container(height=20),
                
                ft.TextButton(
                    content=ft.Text("Volver al inicio"),
                    on_click=lambda _: mostrar_login(),
                    ),
                ], 
                horizontal_alignment="center",
                spacing=5),

                padding=30,
                bgcolor="white",
                border_radius=50,
                width=400,
                )

        
        page.add(verificacion_container)
        page.update()
    
    # Función para la página de registro exitoso
    def registro_exitoso(e):
        # Verificar que las contraseñas coincidan
        if password1.value != password2.value:
            dialog = ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Las contraseñas no coinciden"),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
            return
        
        if not usuario.value or not nombre.value or not password1.value:
            dialog = ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Todos los campos son obligatorios"),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
            return
        
        # Mostrar mensaje de éxito
        dialog = ft.AlertDialog(
            title=ft.Text("Registro exitoso"),
            content=ft.Text(f"Bienvenido {nombre.value}. Ahora elige tu método de verificación."),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
        
        # Ir a la página de verificación
        mostrar_verificacion()
    
    # Página 2: Formulario de registro
    def mostrar_registro(e):
        page.clean()
        
        global usuario, nombre, password1, password2
        usuario = ft.TextField(label="Usuario", width=300)
        nombre = ft.TextField(label="Nombre completo", width=300)
        password1 = ft.TextField(label="Contraseña", password=True, width=300)
        password2 = ft.TextField(label="Confirmar contraseña", password=True, width=300)
        
        registro_container = ft.Container(
            content=ft.Column([
                ft.Text("REGISTRO DE USUARIO", size=30, weight="bold"),
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
            ], 
            horizontal_alignment="center",
            spacing=10),
            padding=30,
            bgcolor="white",
            border_radius=50,
            width=400,
        )
        
        page.add(registro_container)
        page.update()
    
    # Página 1: Login
    def acceso(e):
        if not usuario.value:
            dialog = ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Favor de ingresar un usuario"),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
            return
    
    def mostrar_login():
        page.clean()
        
        global usuario
        usuario= ft.TextField(label="Usuario", width=300)
        
        login_container = ft.Container(
            content=ft.Column([
                ft.Text("INICIAR SESIÓN", size=30, weight="bold"),
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
            ], 
            horizontal_alignment="center",
            spacing=15),
            padding=30,
            bgcolor="white",
            border_radius=50,
            width=400,
        )
        
        page.add(login_container)
        page.update()
    
    # Iniciar con la página de login
    mostrar_login()

ft.app(target=main, assets_dir="assets")