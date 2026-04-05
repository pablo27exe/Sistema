# Modulo para la generación de mapas
import flet as ft
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import sys

# Agregar la ruta base para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar utilidades
from utils.datos import cargar_csv_poblacion, cargar_shapefile_estados


class ModuloMapas:
    def __init__(self, page: ft.Page, usuario_data: dict):
        self.page = page
        self.usuario_data = usuario_data
        self.datos_poblacion = None
        self.gdf_estados = None
        
    def cargar_datos(self):
        """Carga los datos necesarios para los mapas"""
        
        # Cargar datos
        self.datos_poblacion = cargar_csv_poblacion()
        self.gdf_estados = cargar_shapefile_estados()
        
        if self.datos_poblacion is not None:
            print(f"✅ Datos de población cargados: {len(self.datos_poblacion)} registros")
        else:
            print("❌ Error al cargar datos de población")
            
        if self.gdf_estados is not None:
            print(f"✅ Shapefile de estados cargado: {len(self.gdf_estados)} estados")
        else:
            print("❌ Error al cargar shapefile")
        
        return self.datos_poblacion is not None and self.gdf_estados is not None
    
    def generar_mapa_poblacion(self, tipo="estados"):
        """Genera mapa de población por estado"""
        
        # Agregar población por estado
        df_estados = self.datos_poblacion.groupby('clave_estado')['poblacion_total'].sum().reset_index()
        
        # Unir con shapefile
        gdf_mapa = self.gdf_estados.merge(
            df_estados,
            left_on='CVEGEO',
            right_on='clave_estado',
            how='left'
        )
        titulo = "Población por Estado - México 2020"
        columna = 'poblacion_total'
        
        # Crear figura
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        ax.set_axis_off()
        
        # Crear mapa
        gdf_mapa.plot(
            column=columna,
            cmap='YlOrRd',
            legend=True,
            legend_kwds={
                'label': 'Población',
                'shrink': 0.6,
                'pad': 0.02,
                'orientation': 'horizontal'
            },
            ax=ax,
            edgecolor='white',
            linewidth=0.5,
            missing_kwds={'color': 'lightgray', 'label': 'Sin datos'}
        )
        
        ax.set_title(titulo, fontsize=16, fontweight='bold', pad=20)
        
        return fig
    
    def mostrar_mapa_en_flet(self, fig):
        """Convierte una figura de matplotlib a imagen y la muestra en Flet"""
        
        # Convertir figura a imagen
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        # Cerrar figura para liberar memoria
        plt.close(fig)
        
        # Crear imagen en Flet
        temp_path = "temp_mapa.png"
        buf.seek(0)
        with open(temp_path, "wb") as f:
            f.write(buf.getvalue())
        return ft.Image(src=temp_path, width=900, height=700)
    
    def build(self):
        """Construye la interfaz del módulo de mapas"""
        
        # Limpiar página
        self.page.clean()
        self.page.title = "SCINCE - Mapas"
        self.page.bgcolor = "#f5f5f5"
        
        # Botón de volver
        def volver(_):
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from inicio import mostrar_sistema_principal
            mostrar_sistema_principal(self.page, self.usuario_data)
        
        # Barra superior
        topbar = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=volver,
                    tooltip="Volver al inicio"
                ),
                ft.Text("Visualización de Mapas", size=20, weight="bold"),
                ft.Text(f"Usuario: {self.usuario_data['nombre']}", size=12, color="grey"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            bgcolor="white",
            border_radius=ft.BorderRadius(0, 0, 15, 15),
        )
        
        # Cargar datos
        if not self.cargar_datos():
            # Mostrar error si no hay datos
            error_container = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=80, color=ft.Colors.RED_400),
                    ft.Text("No se encontraron datos", size=20, weight="bold"),
                    ft.Text("Asegúrate de tener los archivos CSV y shapefiles en las carpetas correspondientes"),
                    ft.ElevatedButton("Volver", on_click=volver)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True
            )
            self.page.add(topbar, error_container)
            self.page.update()
            return
        
        # Crear mapa nacional
        fig = self.generar_mapa_poblacion(tipo="estados")
        imagen_mapa = self.mostrar_mapa_en_flet(fig)
        
        # Contenedor del mapa
        mapa_container = ft.Container(
            content=imagen_mapa,
            padding=20,
            bgcolor="white",
            border_radius=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200)
        )
        
        # Botón de exportar
        def exportar_mapa(_):
            # Guardar la imagen actual
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mapa_poblacion_{timestamp}.png"
            
            # Crear diálogo para guardar
            def guardar(e):
                # Aquí implementar la lógica de guardado
                pass
            
            dialog = ft.AlertDialog(
                title=ft.Text("Exportar mapa"),
                content=ft.Text(f"Se guardará como: {filename}"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialog)),
                    ft.TextButton("Guardar", on_click=guardar),
                ]
            )
            
            def cerrar_dialogo(dialog):
                dialog.open = False
                self.page.update()
            
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        
        btn_exportar = ft.ElevatedButton(
            "Exportar mapa",
            icon=ft.Icons.SAVE,
            on_click=exportar_mapa,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
        )
        
        # Contenido principal
        contenido = ft.Column([
            topbar,
            ft.Container(height=20),
            ft.Row([ft.Text("📊 Censo de Población 2020", size=14, weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            mapa_container,
            ft.Container(height=20),
            ft.Row([btn_exportar], alignment=ft.MainAxisAlignment.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        self.page.add(
            ft.Container(
                content=contenido,
                expand=True,
                bgcolor="#f5f5f5"
            )
        )
        self.page.update()


# Función para llamar desde inicio.py
def abrir_modulo_mapas(page: ft.Page, usuario_data: dict):
    modulo = ModuloMapas(page, usuario_data)
    modulo.build()