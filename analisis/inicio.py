import flet as ft

def mostrar_bienvenida(page: ft.Page, usuario_data: dict = None, on_cerrar_sesion=None):
    page.clean()

    # Datos de prueba si no se pasa usuario_data
    if usuario_data is None:
        usuario_data = {
            'id': '00000000-0000-0000-0000-000000000000',
            'username': 'usuario_prueba',
            'nombre': 'Usuario De Prueba'
        }

    def cerrar_sesion(_):
        if on_cerrar_sesion:
            on_cerrar_sesion()
        else:
            page.window.close()

    elementos = [
        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=80),
        ft.Text(
            "¡Bienvenido,",
            size=20,
            color=ft.Colors.GREY_600
        ),
        ft.Text(
            usuario_data['nombre'],
            size=32,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(
            "Has iniciado sesión correctamente.",
            size=16,
            color=ft.Colors.GREY_500,
            text_align=ft.TextAlign.CENTER
        ),
        ft.Container(height=20),
        ft.ElevatedButton(
            content=ft.Text("Cerrar sesión"),
            icon=ft.Icons.LOGOUT,
            width=250,
            on_click=cerrar_sesion,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_400
            )
        )
    ]

    bienvenida_container = ft.Container(
        content=ft.Column(
            elementos,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        ),
        padding=40,
        bgcolor="white",
        border_radius=50,
        width=420
    )

    page.add(
        ft.Container(
            content=bienvenida_container,
            alignment=ft.Alignment(0, 0),
            expand=True
        )
    )
    page.update()


# ── Prueba local ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Prueba Bienvenida"
        page.window.maximized = True
        page.bgcolor = "#1a1a2e"
        mostrar_bienvenida(page)

    ft.app(target=main)