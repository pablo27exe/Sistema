# analisis/modulos/graficos.py

import flet as ft
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.datos import cargar_csv_poblacion, cargar_csv_economicas, cargar_csv_salud, NOMBRES_ESTADOS
from utils.mapeos import (
    MAPEO_POBLACION_ABS,
    MAPEO_ECONOMICAS_ABS,
    MAPEO_SALUD_ABS
)
from utils.generar_graficos import preparar_datos_para_grafico, generar_grafico_segun_tipo

# ── Agrupación de subtemas (solo absolutos) ──────────────────────────────────

GRUPOS_POBLACION_ABS = {
    "Totales": ["poblacion_total", "poblacion_femenina", "poblacion_masculina"],
    "0–14 años": ["poblacion_0_2","poblacion_0_4","poblacion_3_5","poblacion_6_11",
                  "poblacion_8_14","poblacion_12_14","poblacion_0_14"],
    "15–29 años": ["poblacion_15_17","poblacion_15_24","poblacion_15_29",
                   "poblacion_18_24"],
    "30–64 años": ["poblacion_30_49","poblacion_50_59","poblacion_60_64",
                   "poblacion_15_64"],
    "65+ años":   ["poblacion_60_mas","poblacion_65_mas","poblacion_70_mas"],
    "Femenino":   [v for v in MAPEO_POBLACION_ABS.values() if "femenina" in v],
    "Masculino":  [v for v in MAPEO_POBLACION_ABS.values() if "masculina" in v],
}

GRUPOS_ECONOMICAS_ABS = {
    "PEA":         [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("pea")],
    "Ocupados":    [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("ocup")],
    "Desocupados": [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("desoc")],
    "No PEA":      [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("no_pea")],
}

GRUPOS_SALUD_ABS = {
    "Afiliación": ["poblacion_afiliada_servicios_salud", "poblacion_sin_afiliacion"],
    "Por institución": [
        "poblacion_afiliacion_imss",
        "poblacion_afiliacion_imss_bienestar",
        "poblacion_afiliacion_issste",
        "poblacion_afiliacion_issste_estatal",
        "poblacion_afiliacion_insabi",
        "poblacion_afiliacion_pemex_defensa_marina",
        "poblacion_afiliacion_privada",
        "poblacion_afiliacion_otra",
    ],
}

SIDEBAR_TEMAS = {
    "Población": GRUPOS_POBLACION_ABS,
    "Salud": GRUPOS_SALUD_ABS,
    "Economía": GRUPOS_ECONOMICAS_ABS,
}

FORMATOS_GUARDADO = ["PNG", "PDF", "JPG"]


# ── Módulo principal ────────────────────────────────────────────────────────

class ModuloGraficos:
    def __init__(self, page: ft.Page, usuario_data: dict):
        self.page = page
        self.usuario_data = usuario_data

        # Datos
        self.dfs = {}

        # Estado de la UI
        self.columna_activa = None
        self.tema_activo = None
        self.titulo_activo = "Selecciona un indicador"
        self.nivel_actual = None
        self.estado_seleccionado = None
        self.tipo_grafico = "bar_chart"

        # Referencias
        self.img_ref = ft.Ref[ft.Image]()
        self.spinner_ref = ft.Ref[ft.ProgressRing]()
        self.titulo_grafico_ref = ft.Ref[ft.Text]()
        self.sidebar_col_ref = ft.Ref[ft.Column]()
        self.placeholder_ref = ft.Ref[ft.Container]()

        # Estado del árbol sidebar
        self._tema_abierto = None
        self._grupo_abierto = None

        # Estado del selector de nivel
        self._estados_abierto = False
        
        # Botones de gráficos
        self.btn_bar_chart = None
        self.btn_box_plot = None
        self.btn_density = None
        self.btn_percentage = None
        self.btn_histogram = None
        self.btn_line_chart = None

    def _limpiar_temporales(self):
        """Elimina todas las imágenes temporales al iniciar el módulo"""
        directorio = os.path.dirname(__file__)
        for archivo in os.listdir(directorio):
            if archivo.startswith("_grafico_temp_") and archivo.endswith(".png"):
                try:
                    os.remove(os.path.join(directorio, archivo))
                    print(f"Eliminado temporal: {archivo}")
                except Exception as e:
                    print(f"No se pudo eliminar {archivo}: {e}")

    # ── Carga de datos ──────────────────────────────────────────────────────

    def _cargar_datos_thread(self, on_done):
        try:
            print("\nCargando datos para gráficos...")
            self.dfs["poblacion"] = cargar_csv_poblacion("abs")
            self.dfs["economicas"] = cargar_csv_economicas("abs")
            self.dfs["salud"] = cargar_csv_salud("abs")
            exito = self.dfs["poblacion"] is not None
        except Exception as e:
            print(f"Error cargando datos: {e}")
            exito = False
        on_done(exito)

    def cargar_datos_async(self, on_done):
        threading.Thread(target=self._cargar_datos_thread, args=(on_done,), daemon=True).start()

    def _df_para_tema(self, tema: str):
        return self.dfs.get(tema)

    # ── Sidebar (simplificado - solo temas y grupos) ────────────────────────

    def _label(self, texto: str) -> str:
        return texto.replace("_", " ").title()

    def _build_sidebar(self) -> ft.Column:
        items = []

        for tema, grupos in SIDEBAR_TEMAS.items():
            tema_abierto = self._tema_abierto == tema
            tema_key = "poblacion" if tema == "Población" else "economicas" if tema == "Economía" else "salud"

            def _on_tema(e, t=tema):
                self._tema_abierto = None if self._tema_abierto == t else t
                self._grupo_abierto = None
                self._refrescar_sidebar()

            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(tema, size=14, weight="bold",
                                color=ft.Colors.BLUE_800 if tema_abierto else ft.Colors.BLACK),
                        ft.Icon(ft.Icons.EXPAND_LESS if tema_abierto else ft.Icons.EXPAND_MORE, size=18),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50 if tema_abierto else "white",
                    on_click=_on_tema,
                    ink=True,
                )
            )

            if not tema_abierto:
                continue

            for grupo, columnas in grupos.items():
                grupo_abierto = self._grupo_abierto == grupo

                def _on_grupo(e, g=grupo):
                    self._grupo_abierto = None if self._grupo_abierto == g else g
                    self._refrescar_sidebar()

                items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(grupo, size=13,
                                    color=ft.Colors.BLUE_600 if grupo_abierto else ft.Colors.GREY_700),
                            ft.Icon(ft.Icons.EXPAND_LESS if grupo_abierto else ft.Icons.EXPAND_MORE, size=16),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.only(left=20, right=12, top=7, bottom=7),
                        bgcolor=ft.Colors.BLUE_50 if grupo_abierto else "transparent",
                        border_radius=6,
                        on_click=_on_grupo,
                        ink=True,
                    )
                )

                if not grupo_abierto:
                    continue

                for col in columnas:
                    activa = col == self.columna_activa

                    def _on_col(e, c=col, t=tema_key):
                        print(f"📊 Indicador seleccionado: {c}")
                        self.columna_activa = c
                        self.tema_activo = t
                        self.titulo_activo = self._label(c)
                        self._refrescar_sidebar()
                        if self.titulo_grafico_ref.current:
                            self.titulo_grafico_ref.current.value = self.titulo_activo
                        print(f"   columna_activa={self.columna_activa}, tema_activo={self.tema_activo}")

                    items.append(
                        ft.Container(
                            content=ft.Text(self._label(col), size=11,
                                            color=ft.Colors.BLUE_700 if activa else ft.Colors.GREY_700,
                                            weight="bold" if activa else "normal",
                                            overflow=ft.TextOverflow.ELLIPSIS),
                            padding=ft.padding.only(left=44, right=8, top=4, bottom=4),
                            bgcolor=ft.Colors.BLUE_100 if activa else "transparent",
                            border_radius=4,
                            on_click=_on_col,
                            ink=True,
                        )
                    )

        items.append(ft.Divider(height=1, color=ft.Colors.GREY_300))
        items.append(ft.Text("Nivel", size=13, weight="bold", color=ft.Colors.GREY_600))

        def on_nacional(e):
            self.nivel_actual = "nacional"
            self._estados_abierto = False
            self._refrescar_sidebar()

        def on_estatal(e):
            self.nivel_actual = "estatal"
            self._estados_abierto = not self._estados_abierto
            self._refrescar_sidebar()

        items.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=14,
                            color=ft.Colors.GREEN_700 if self.nivel_actual == "nacional" else ft.Colors.GREY_500),
                    ft.Text("Nacional", size=13,
                            color=ft.Colors.GREEN_700 if self.nivel_actual == "nacional" else ft.Colors.BLACK),
                ], spacing=8),
                padding=ft.padding.only(left=12, right=12, top=6, bottom=6),
                on_click=on_nacional,
                ink=True,
            )
        )

        items.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=14,
                            color=ft.Colors.GREEN_700 if self.nivel_actual == "estatal" else ft.Colors.GREY_500),
                    ft.Text("Estatal", size=13,
                            color=ft.Colors.GREEN_700 if self.nivel_actual == "estatal" else ft.Colors.BLACK),
                    ft.Icon(ft.Icons.EXPAND_MORE if not self._estados_abierto else ft.Icons.EXPAND_LESS, size=16,
                            color=ft.Colors.GREY_600),
                ], spacing=8),
                padding=ft.padding.only(left=12, right=12, top=6, bottom=6),
                on_click=on_estatal,
                ink=True,
            )
        )

        if self.nivel_actual == "estatal" and self._estados_abierto:
            for clave, nombre in NOMBRES_ESTADOS.items():
                def on_estado(e, c=clave, n=nombre):
                    self.estado_seleccionado = c
                    self._estados_abierto = False
                    self._refrescar_sidebar()

                items.append(
                    ft.Container(
                        content=ft.Text(nombre, size=12, color=ft.Colors.GREY_700),
                        padding=ft.padding.only(left=32, right=12, top=4, bottom=4),
                        on_click=on_estado,
                        ink=True,
                    )
                )

        return ft.Column(items, spacing=2, scroll=ft.ScrollMode.AUTO)

    def _refrescar_sidebar(self):
        if self.sidebar_col_ref.current:
            self.sidebar_col_ref.current.controls = self._build_sidebar().controls
            self.page.update()

    # ── Generación de gráficos ──────────────────────────────────────────────

    def _generar_grafico(self):
        """Genera el gráfico según el tipo seleccionado"""
        print(f"🔧 _generar_grafico - Iniciando")
        print(f"   tema_activo={self.tema_activo}, columna_activa={self.columna_activa}")
        
        df = self._df_para_tema(self.tema_activo)
        print(f"   df obtenido: {df is not None}")
        if df is not None:
            print(f"   columnas de df: {df.columns.tolist()[:5]}...")
            print(f"   '{self.columna_activa}' en columnas: {self.columna_activa in df.columns}")
        
        if df is None or self.columna_activa not in df.columns:
            print(f"Error: df es None o columna no existe")
            return None
        
        print(f"Preparando datos para gráfico...")
        datos = preparar_datos_para_grafico(
            df, self.columna_activa, self.nivel_actual, 
            self.estado_seleccionado, NOMBRES_ESTADOS
        )
        print(f"   datos obtenidos: {datos is not None}, len={len(datos) if datos is not None else 0}")
        
        if datos is None or len(datos) == 0:
            print(f"Error: No hay datos para el gráfico")
            return None
        
        if self.nivel_actual == "nacional":
            titulo = f"{self.titulo_activo} - Nacional"
        else:
            nombre_estado = NOMBRES_ESTADOS.get(self.estado_seleccionado, self.estado_seleccionado)
            titulo = f"{self.titulo_activo} - {nombre_estado}"
        
        print(f"Generando gráfico tipo: {self.tipo_grafico}")
        fig = generar_grafico_segun_tipo(self.tipo_grafico, datos, titulo)
        print(f"   figura generada: {fig is not None}")
        
        return fig

    def _mostrar_grafico(self):
        """Genera y muestra el gráfico"""
        print(f"_mostrar_grafico llamado")
        print(f"   columna_activa={self.columna_activa}, tema_activo={self.tema_activo}, nivel_actual={self.nivel_actual}")
        if self.columna_activa is None or self.tema_activo is None:
            return
        if self.nivel_actual is None:
            return
        if self.nivel_actual == "estatal" and self.estado_seleccionado is None:
            return
        
        print("Todos los criterios cumplidos, generando gráfico...")
        
        if self.spinner_ref.current:
            self.spinner_ref.current.visible = True
        if self.img_ref.current:
            self.img_ref.current.visible = False
        if self.placeholder_ref.current:
            self.placeholder_ref.current.visible = False
        self.page.update()
        
        def _trabajo():
            fig = self._generar_grafico()
            
            def _actualizar():
                if self.spinner_ref.current:
                    self.spinner_ref.current.visible = False
                if fig:
                    timestamp = int(time.time() * 1000)
                    temp = os.path.join(os.path.dirname(__file__), f"_grafico_temp_{timestamp}.png")
                    fig.savefig(temp, format="png", dpi=130, bbox_inches="tight")
                    plt.close(fig)
                    
                    if self.img_ref.current:
                        self.img_ref.current.src = temp
                        self.img_ref.current.visible = True
                    if self.placeholder_ref.current:
                        self.placeholder_ref.current.visible = False
                else:
                    if self.placeholder_ref.current:
                        self.placeholder_ref.current.visible = True
                self.page.update()
            
            self.page.run_thread(_actualizar)
        
        threading.Thread(target=_trabajo, daemon=True).start()

    def _guardar_grafico(self, formato: str):
        """Guarda el gráfico en la carpeta C:/Graficos_SCINCE/"""
        if self.columna_activa is None or self.tema_activo is None:
            return
        if self.nivel_actual is None:
            return
        if self.nivel_actual == "estatal" and self.estado_seleccionado is None:
            return
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_limpio = self.titulo_activo.replace(" ", "_").replace("/", "_")
        nombre = f"grafico_{self.tipo_grafico}_{nombre_limpio}_{timestamp}.{formato.lower()}"
        
        directorio = "C:/Graficos_SCINCE"
        os.makedirs(directorio, exist_ok=True)
        destino = os.path.join(directorio, nombre)
        
        fig = self._generar_grafico()
        if fig is None:
            return
        
        dpi = 200 if formato in ("PNG", "JPG") else 150
        fig.savefig(destino, format=formato.lower(), dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        
        def mostrar_mensaje():
            def cerrar_dialogo(dialog):
                dialog.open = False
                self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Gráfico guardado"),
                content=ft.Text(f"Archivo guardado en:\n{destino}"),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog))
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        
        self.page.run_thread(mostrar_mensaje)

    def _dialogo_guardar(self, _):
        """Diálogo para seleccionar formato de guardado"""
        if self.columna_activa is None or self.tema_activo is None:
            return
        if self.nivel_actual is None:
            return
        
        formato_sel = ft.Ref[ft.RadioGroup]()
        
        def confirmar(e):
            dlg.open = False
            self.page.update()
            fmt = formato_sel.current.value or "PNG"
            threading.Thread(target=self._guardar_grafico, args=(fmt,), daemon=True).start()
        
        def cancelar(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Guardar gráfico"),
            content=ft.Column([
                ft.Text("Selecciona el formato:"),
                ft.RadioGroup(
                    ref=formato_sel,
                    value="PNG",
                    content=ft.Column([ft.Radio(value=f, label=f) for f in FORMATOS_GUARDADO]),
                ),
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.TextButton("Guardar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _on_tipo_grafico(self, tipo: str, btn_activo, btns_anteriores):
        """Cambia el tipo de gráfico y actualiza colores de botones"""
        print(f"Click en gráfico: {tipo}")
        print(f"   columna_activa={self.columna_activa}, tema_activo={self.tema_activo}, nivel_actual={self.nivel_actual}")
        self.tipo_grafico = tipo
        for btn in btns_anteriores:
            if btn:
                btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK)
        if btn_activo:
            btn_activo.style = ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
        self.page.update()
        self._mostrar_grafico()

    # ── Build ────────────────────────────────────────────────────────────────

    def build(self):
        self._limpiar_temporales()
        self.page.clean()
        self.page.title = "SCINCE – Gráficos"
        self.page.bgcolor = "#f5f5f5"
        self.page.padding = 0
        self.page.expand = True

        def volver(_):
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from inicio import mostrar_sistema_principal
            mostrar_sistema_principal(self.page, self.usuario_data)

        # Topbar
        topbar = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=volver, tooltip="Volver"),
                    ft.Text("Visualización de Gráficos", size=18, weight="bold"),
                ]),
                ft.Text(self.usuario_data["nombre"], size=12, color="grey"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor="white",
            border_radius=ft.BorderRadius(0, 0, 15, 15),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200),
        )

        # ── Barra de botones de tipo de gráfico y guardar ──
        self.btn_bar_chart = ft.ElevatedButton(
            "Barras",
            icon=ft.Icons.BAR_CHART,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
        )
        self.btn_box_plot = ft.ElevatedButton(
            "Cajas",
            icon=ft.Icons.SHOW_CHART,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK),
        )
        self.btn_density = ft.ElevatedButton(
            "Densidad",
            icon=ft.Icons.TIMELINE,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK),
        )
        self.btn_percentage = ft.ElevatedButton(
            "Porcentaje",
            icon=ft.Icons.PERCENT,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK),
        )
        self.btn_histogram = ft.ElevatedButton(
            "Histograma",
            icon=ft.Icons.STACKED_BAR_CHART,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK),
        )
        self.btn_line_chart = ft.ElevatedButton(
            "Líneas",
            icon=ft.Icons.SSID_CHART,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_400, color=ft.Colors.BLACK),
        )
        
        btn_guardar = ft.ElevatedButton(
            "Guardar",
            icon=ft.Icons.SAVE_ALT,
            on_click=self._dialogo_guardar,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
        )

        btns_graficos = [self.btn_bar_chart, self.btn_box_plot, self.btn_density, 
                         self.btn_percentage, self.btn_histogram, self.btn_line_chart]

        self.btn_bar_chart.on_click = lambda _: self._on_tipo_grafico("bar_chart", self.btn_bar_chart, btns_graficos)
        self.btn_box_plot.on_click = lambda _: self._on_tipo_grafico("box_plot", self.btn_box_plot, btns_graficos)
        self.btn_density.on_click = lambda _: self._on_tipo_grafico("density", self.btn_density, btns_graficos)
        self.btn_percentage.on_click = lambda _: self._on_tipo_grafico("percentage", self.btn_percentage, btns_graficos)
        self.btn_histogram.on_click = lambda _: self._on_tipo_grafico("histogram", self.btn_histogram, btns_graficos)
        self.btn_line_chart.on_click = lambda _: self._on_tipo_grafico("line_chart", self.btn_line_chart, btns_graficos)

        # Contenedor de botones
        botones_graficos = ft.Container(
            content=ft.Row(
                btns_graficos + [btn_guardar],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                wrap=True,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor="white",
            border_radius=15,
            margin=ft.margin.only(bottom=10),
        )

        # ── Sidebar ──
        sidebar = ft.Container(
            content=ft.Column([
                ft.Text("Indicadores", size=13, weight="bold", color=ft.Colors.GREY_600),
                ft.Divider(height=1),
                ft.Column(
                    ref=self.sidebar_col_ref,
                    controls=self._build_sidebar().controls,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    spacing=2,
                ),
                ft.Divider(height=1),
            ], spacing=8, expand=True),
            width=280,
            padding=ft.padding.all(12),
            bgcolor="white",
            border_radius=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200),
        )

        # ── Área del gráfico ──
        area_grafico = ft.Container(
            content=ft.Stack([
                ft.Image(ref=self.img_ref, src=None, fit="contain", expand=True, visible=False),
                ft.Container(
                    ref=self.placeholder_ref,
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHOW_CHART, size=80, color=ft.Colors.GREY_300),
                        ft.Text(
                            "Selecciona un indicador y tipo de gráfico",
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_400,
                            size=16,
                            weight="bold",
                        ),
                        ft.Text(
                            "Elige un indicador, selecciona nivel (Nacional/Estatal)\ny haz clic en el tipo de gráfico",
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_400,
                            size=12,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    expand=True,
                    visible=True,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.ProgressRing(ref=self.spinner_ref, visible=False, width=48, height=48),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    expand=True,
                ),
            ], expand=True),
            expand=True,
            bgcolor="white",
            border_radius=15,
            padding=16,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200),
        )

        titulo_grafico = ft.Text(
            ref=self.titulo_grafico_ref,
            value=self.titulo_activo,
            size=15,
            weight="bold",
            color=ft.Colors.BLUE_900,
        )

        # Layout principal
        contenido_columna = ft.Column(
            [botones_graficos, ft.Row([titulo_grafico], alignment=ft.MainAxisAlignment.CENTER), area_grafico],
            expand=True,
            spacing=8,
        )

        cuerpo = ft.Row([sidebar, contenido_columna], expand=True, spacing=16)

        pagina_principal = ft.Column(
            [topbar, ft.Container(content=cuerpo, expand=True, padding=ft.padding.all(16))],
            expand=True,
            spacing=0,
        )

        self.page.add(pagina_principal)
        self.page.update()

        # Carga de datos en segundo plano
        def _on_datos_listos(exito):
            if not exito:
                print("No se encontraron algunos archivos de datos")
            else:
                print("\nTodos los datos cargados exitosamente")
                print("Esperando selección de usuario...")

        self.cargar_datos_async(_on_datos_listos)

def abrir_modulo_graficos(page: ft.Page, usuario_data: dict):
    ModuloGraficos(page, usuario_data).build()