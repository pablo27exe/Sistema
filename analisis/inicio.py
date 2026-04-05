import flet as ft
from datetime import datetime
import sys

def obtener_saludo():
    hora_actual = datetime.now().hour
    if 5 <= hora_actual < 12:
        return "¡Buenos días"
    elif 12 <= hora_actual <= 18:
        return "¡Buenas tardes"
    else:
        return "¡Buenas noches"


def mostrar_sistema_principal(page: ft.Page, usuario_data: dict, on_cerrar_sesion=None):
    page.clean()
    page.title = "Sistema SCINCE"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f5f5f5"
    page.padding = 0

    def cerrar_dialogo(dialog):
        """Cierra un diálogo correctamente"""
        if dialog:
            dialog.open = False
            page.update()

    def crear_dialogo(titulo, mensaje, tipo="info"):
        """Crea un diálogo estandarizado como en tu ejemplo"""
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
        page.overlay.append(dialog)  # ← Clave: usar overlay en lugar de page.dialog
        dialog.open = True
        page.update()
        return dialog

    def confirmar_cerrar_sesion(_):
        def on_confirmar(e):
            dialog.open = False
            page.update()
            page.window.destroy()
            sys.exit(0)

        def on_cancelar(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cerrar sesión", color=ft.Colors.RED_400),
            content=ft.Text("¿Estás seguro de que deseas cerrar sesión?"),
            actions=[
                ft.TextButton("Cancelar", on_click=on_cancelar),
                ft.TextButton(
                    "Sí, cerrar sesión",
                    on_click=on_confirmar,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialog)  # ← Usar overlay
        dialog.open = True
        page.update()

    # --- Barra superior ---
    topbar = ft.Container(
        content=ft.Row([
            ft.Text("Sistema de Análisis de datos", size=18, weight="bold"),
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
                    content=ft.Text("Cerrar sesión", size=12),
                    on_click=confirmar_cerrar_sesion,
                )
            ], spacing=10)
        ], alignment="spaceBetween"),
        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        bgcolor="white",
        border_radius=ft.BorderRadius(0, 0, 15, 15),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200)
    )

    saludo = ft.Text(
        f"{obtener_saludo()}, {usuario_data['nombre']}!",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )

    subtitulo = ft.Text(
        "Selecciona un módulo para comenzar",
        size=14,
        color=ft.Colors.GREY_600
    )

    # --- Funciones para abrir cada módulo con diálogo ---
    def abrir_gestion(e):
        crear_dialogo(
            "Gestión de Datos", 
            "Módulo de gestión de datos - Funcionalidad en desarrollo",
            "info"
        )

    def abrir_graficos(e):
        crear_dialogo(
            "Generar Gráficos", 
            "Módulo de generación de gráficos - Funcionalidad en desarrollo",
            "info"
        )

    def abrir_reportes(e):
        crear_dialogo(
            "Reportes", 
            "Módulo de reportes - Funcionalidad en desarrollo",
            "info"
        )

    # En inicio.py, modificar la función abrir_mapas:

    def abrir_mapas(e):
        from modulos.mapas import abrir_modulo_mapas
        abrir_modulo_mapas(page, usuario_data)

    # --- Card con ícono e interacción ---
    def modulo_card(titulo, descripcion, icono_path, color_fondo, on_click):
        return ft.Container(
            content=ft.Column([
                ft.Image(
                    src=icono_path,
                    width=52,
                    height=52,
                    fit="contain",
                ),
                ft.Text(titulo, size=18, weight="bold"),
                ft.Text(
                    descripcion,
                    size=12,
                    color="grey",
                    text_align=ft.TextAlign.CENTER
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            padding=30,
            width=280,
            height=220,
            bgcolor="white",
            border_radius=15,
            on_click=on_click,
            ink=True,
        )

    cards = ft.Row([
        modulo_card(
            "Gestión de datos",
            "Filtra por sector y alcance",
            "analisis/assets/datos.ico",
            ft.Colors.BLUE_100,
            abrir_gestion
        ),
        modulo_card(
            "Generar gráficos",
            "Visualizaciones con matplotlib",
            "analisis/assets/grafico.ico",
            ft.Colors.GREEN_100,
            abrir_graficos
        ),
        modulo_card(
            "Reportes",
            "Exportar a Excel y PDF",
            "analisis/assets/reporte.ico",
            ft.Colors.ORANGE_100,
            abrir_reportes
        ),
        modulo_card(
            "Mapas",
            "Visualización geográfica",
            "analisis/assets/mapa.ico",
            ft.Colors.RED_100,
            abrir_mapas
        ),
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


def mostrar_bienvenida(page: ft.Page, usuario_data: dict, on_cerrar_sesion=None):
    mostrar_sistema_principal(page, usuario_data, on_cerrar_sesion)


def iniciar_sesion(page: ft.Page, usuario_data: dict = None):
    if usuario_data is None:
        usuario_data = {
            'id': '00000000-0000-0000-0000-000000000000',
            'username': 'PabloM',
            'nombre': 'Pablo Munguía'
        }
    mostrar_sistema_principal(page, usuario_data)


if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Sistema SCINCE"
        page.window.maximized = True
        page.bgcolor = "#f5f5f5"
        iniciar_sesion(page)

    ft.app(target=main)