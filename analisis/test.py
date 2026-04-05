import flet as ft

def test(page: ft.Page):
    page.title = "Test"
    
    estado_seleccionado = ft.Text("Estado: Puebla")
    
    def on_estado_seleccionado(e):
        estado_seleccionado.value = f"Estado: {e.control.text}"
        page.update()
        print(f"Estado seleccionado: {e.control.text}")
    
    # Menú de estados
    estados_menu = ft.PopupMenuButton(
        icon=ft.Icons.ARROW_DROP_DOWN,
        items=[
            ft.PopupMenuItem(text="Aguascalientes", on_click=on_estado_seleccionado),
            ft.PopupMenuItem(text="Baja California", on_click=on_estado_seleccionado),
            ft.PopupMenuItem(text="CDMX", on_click=on_estado_seleccionado),
            ft.PopupMenuItem(text="México", on_click=on_estado_seleccionado),
            ft.PopupMenuItem(text="Puebla", on_click=on_estado_seleccionado),
        ]
    )
    
    page.add(ft.Row([ft.Text("Seleccionar estado:"), estados_menu, estado_seleccionado]))
    page.update()

ft.app(target=test)