import flet as ft

def mostrar_bienvenida(page: ft.Page, usuario_data: dict, on_cerrar_sesion=None):
    """Redirige directamente al sistema principal (la bienvenida está integrada allí)"""
    mostrar_sistema_principal(page, usuario_data, on_cerrar_sesion)


def mostrar_sistema_principal(page: ft.Page, usuario_data: dict, on_cerrar_sesion=None):
    """Pantalla principal del Sistema SCINCE con barra superior fija (bienvenida integrada)"""
    page.clean()
    
    page.title = "Sistema SCINCE"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f5f5f5"
    page.padding = 0

    def cerrar_sesion(_):
        if on_cerrar_sesion:
            on_cerrar_sesion()
        else:
            page.window.close()

    # --- Barra superior con info de usuario (bienvenida integrada) ---
    topbar = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Text("📊", size=24),
                ft.Text("Sistema SCINCE · Análisis de datos", size=18, weight="bold"),
            ]),
            ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(usuario_data['nombre'][:2].upper(), size=12),
                            bgcolor=ft.Colors.BLUE_200,
                            radius=18
                        ),
                        ft.Column([
                            ft.Text(usuario_data['nombre'], size=14, weight="bold"),
                            ft.Text(usuario_data['username'], size=11, color="grey"),
                        ], spacing=0)
                    ]),
                    padding=ft.Padding.only(right=15)
                ),
                ft.TextButton(
                    content=ft.Row([
                        ft.Text("🚪", size=16),
                        ft.Text("Cerrar sesión", size=12),
                    ], spacing=5),
                    on_click=cerrar_sesion,
                )
            ], spacing=10)
        ], alignment="spaceBetween"),
        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        bgcolor="white",
        border_radius=ft.BorderRadius(0, 0, 15, 15),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200)
    )

    # Saludo de bienvenida en la página principal
    saludo = ft.Text(
        f"¡Hola {usuario_data['nombre']}!",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )
    
    subtitulo = ft.Text(
        "Selecciona un módulo para comenzar",
        size=14,
        color=ft.Colors.GREY_600
    )

    def modulo_card(titulo, descripcion, color):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        width=50,
                        height=50,
                        bgcolor=color,
                        border_radius=25,
                    ),
                    ft.Text(titulo, size=18, weight="bold"),
                    ft.Text(descripcion, size=12, color="grey", text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                padding=30,
                width=280,
                height=220,
                bgcolor="white",
                border_radius=15
            ),
            elevation=5,
        )

    cards = ft.Row([
        modulo_card("Gestión de datos", "Filtra por sector y alcance", ft.Colors.BLUE_100),
        modulo_card("Generar gráficos", "Visualizaciones con matplotlib", ft.Colors.GREEN_100),
        modulo_card("Reportes", "Exportar a Excel", ft.Colors.ORANGE_100),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=30, wrap=True)

    contenido_principal = ft.Column([
        topbar,
        ft.Container(height=30),
        ft.Column([
            saludo,
            subtitulo,
            ft.Container(height=30),
            cards,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    ], spacing=0, expand=True)

    page.add(
        ft.Container(
            content=contenido_principal,
            expand=True,
            bgcolor="#f5f5f5"
        )
    )
    page.update()


def iniciar_sesion(page: ft.Page, usuario_data: dict = None):
    """Inicia la aplicación mostrando directamente el sistema principal"""
    
    if usuario_data is None:
        usuario_data = {
            'id': '00000000-0000-0000-0000-000000000000',
            'username': 'usuario_prueba',
            'nombre': 'Usuario De Prueba'
        }
    
    def al_cerrar_sesion():
        iniciar_sesion(page, None)
    
    mostrar_sistema_principal(page, usuario_data, al_cerrar_sesion)


if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Sistema SCINCE"
        page.window.maximized = True
        page.bgcolor = "#f5f5f5"
        iniciar_sesion(page)

    ft.app(target=main)