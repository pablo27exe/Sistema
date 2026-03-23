import flet as ft
#import sys

def mostrar_bienvenida(page: ft.Page, usuario_data: dict, on_cerrar_sesion = None):
    page.clean()
    
    def cerrar_sesion(_):
        if on_cerrar_sesion(_):
            on_cerrar_sesion()
        else:
            page.window.destroy()
    
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