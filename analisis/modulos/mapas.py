# analisis/modulos/mapas.py
import time
import flet as ft
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.datos import cargar_csv_poblacion, cargar_csv_economicas, cargar_csv_salud
from utils.datos import cargar_shapefile_estados, cargar_shapefile_municipios, NOMBRES_ESTADOS
from utils.mapeos import (
    MAPEO_POBLACION_ABS, MAPEO_POBLACION_REL,
    MAPEO_ECONOMICAS_ABS, MAPEO_ECONOMICAS_REL,
    MAPEO_SALUD_REL
)

# ── Agrupación de subtemas ──────────────────────────────────────────────────

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

GRUPOS_POBLACION_REL = {
    "Indicadores": ["porcentaje_femenino","porcentaje_masculino",
                    "relacion_hombres_mujeres","razon_dependencia_total",
                    "razon_dependencia_infantil","razon_dependencia_vejez",
                    "edad_mediana_total","indice_envejecimiento_total"],
    "0–14 años":   [v for v in MAPEO_POBLACION_REL.values() if "_0_" in v or "_3_5" in v],
    "15–64 años":  [v for v in MAPEO_POBLACION_REL.values() if "15_" in v or "18_" in v],
    "65+ años":    [v for v in MAPEO_POBLACION_REL.values() if "60_mas" in v or "65_mas" in v],
    "Femenino":    [v for v in MAPEO_POBLACION_REL.values() if "femenino" in v],
    "Masculino":   [v for v in MAPEO_POBLACION_REL.values() if "masculino" in v],
}

GRUPOS_ECONOMICAS_ABS = {
    "PEA":         [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("pea")],
    "Ocupados":    [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("ocup")],
    "Desocupados": [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("desoc")],
    "No PEA":      [v for v in MAPEO_ECONOMICAS_ABS.values() if v.startswith("no_pea")],
}

GRUPOS_ECONOMICAS_REL = {
    "PEA %":         [v for v in MAPEO_ECONOMICAS_REL.values() if "pea" in v],
    "Ocupados %":    [v for v in MAPEO_ECONOMICAS_REL.values() if "ocupad" in v],
    "Desocupados %": [v for v in MAPEO_ECONOMICAS_REL.values() if "desocup" in v],
    "No PEA %":      [v for v in MAPEO_ECONOMICAS_REL.values() if "no_pea" in v],
}

GRUPOS_SALUD_REL = {
    "Afiliación": list(MAPEO_SALUD_REL.values()),
}

SIDEBAR_TEMAS = {
    "Población": {
        "Absoluto": GRUPOS_POBLACION_ABS,
        "Relativo": GRUPOS_POBLACION_REL,
    },
    "Salud": {
        "Relativo": GRUPOS_SALUD_REL,
    },
    "Economía": {
        "Absoluto": GRUPOS_ECONOMICAS_ABS,
        "Relativo": GRUPOS_ECONOMICAS_REL,
    },
}

FORMATOS_GUARDADO = ["PNG", "PDF", "JPG"]


# ── Módulo principal ────────────────────────────────────────────────────────

class ModuloMapas:
    def __init__(self, page: ft.Page, usuario_data: dict):
        self.page         = page
        self.usuario_data = usuario_data

        # Datos
        self.gdf_estados    = None
        self.gdf_municipios = None
        self.dfs            = {}

        # Estado de la UI (TODO vacío al inicio)
        self.columna_activa = None
        self.tema_activo    = None
        self.titulo_activo  = "Selecciona un indicador"
        self.nivel_actual   = None
        self.estado_seleccionado = None

        # Referencias a widgets
        self.img_ref          = ft.Ref[ft.Image]()
        self.spinner_ref      = ft.Ref[ft.ProgressRing]()
        self.titulo_mapa_ref  = ft.Ref[ft.Text]()
        self.sidebar_col_ref  = ft.Ref[ft.Column]()
        self.placeholder_ref  = ft.Ref[ft.Container]()

        # Estado del árbol sidebar
        self._tema_abierto  = None
        self._tipo_abierto  = None
        self._grupo_abierto = None
        
        # Estado del selector de nivel en sidebar
        self._nivel_abierto = False
        self._estados_abierto = False
        self.nivel_texto = ft.Text("Seleccionar nivel", size=13, color=ft.Colors.BLUE_800)
        self.estado_texto = ft.Text("Seleccionar estado", size=12, color=ft.Colors.GREY_700)
        
    def _limpiar_temporales(self):
        """Elimina todas las imágenes temporales al iniciar el módulo"""
        directorio = os.path.dirname(__file__)
        for archivo in os.listdir(directorio):
            if archivo.startswith("_mapa_temp_") and archivo.endswith(".png"):
                try:
                    os.remove(os.path.join(directorio, archivo))
                    #print(f"Eliminado temporal: {archivo}")
                except Exception as e:
                    print(f"No se pudo eliminar {archivo}: {e}")
        
    def _log_seleccion(self):
        """Muestra en consola el estado actual de la selección"""
        estado_nombre = NOMBRES_ESTADOS.get(self.estado_seleccionado, 'Ninguno') if self.estado_seleccionado else 'Ninguno'
        print(f"\n{'='*50}")
        print(f"ESTADO ACTUAL DE SELECCIÓN:")
        print(f"   Tema: {self.tema_activo}")
        print(f"   Columna: {self.columna_activa}")
        print(f"   Título: {self.titulo_activo}")
        print(f"   Nivel: {self.nivel_actual}")
        print(f"   Estado: {self.estado_seleccionado} ({estado_nombre})")
        print(f"{'='*50}")

    # ── Carga de datos ──────────────────────────────────────────────────────

    def _cargar_datos_thread(self, on_done):
        try:
            #print("\nCargando shapefiles...")
            self.gdf_estados    = cargar_shapefile_estados()
            self.gdf_municipios = cargar_shapefile_municipios()

            #print("\nCargando CSVs...")
            self.dfs["poblacion_abs"]  = cargar_csv_poblacion("abs")
            self.dfs["poblacion_rel"]  = cargar_csv_poblacion("rel")
            self.dfs["economicas_abs"] = cargar_csv_economicas("abs")
            self.dfs["economicas_rel"] = cargar_csv_economicas("rel")
            self.dfs["salud_abs"]      = cargar_csv_salud("abs")
            self.dfs["salud_rel"]      = cargar_csv_salud("rel")

            exito = all([
                self.gdf_estados is not None,
                self.dfs["poblacion_abs"] is not None,
            ])
            
            if exito:
                print("\nTodos los datos cargados correctamente")
            else:
                print("\nAlgunos datos no se cargaron correctamente")
                
        except Exception as e:
            print(f"Error cargando datos: {e}")
            exito = False
        on_done(exito)

    def cargar_datos_async(self, on_done):
        threading.Thread(
            target=self._cargar_datos_thread,
            args=(on_done,),
            daemon=True
        ).start()

    # ── Métodos auxiliares que devuelven la figura (para guardar) ───────────

    def _generar_figura_nacional(self, columna: str, tema: str):
        """Genera y retorna la figura del mapa nacional (no guarda archivo)"""
        df = self._df_para_tema(tema)
        if df is None or columna not in df.columns:
            print(f"Error: Columna '{columna}' no encontrada en tema '{tema}'")
            return None
        if "clave_estado" not in df.columns:
            print("Error: Falta columna 'clave_estado'")
            return None

        df_agg = df.groupby("clave_estado")[columna].sum().reset_index()
        gdf = self.gdf_estados.merge(df_agg, left_on="CVEGEO", right_on="clave_estado", how="left")

        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_axis_off()
        
        from matplotlib.ticker import FuncFormatter
        def formato_miles(x, p):
            if x >= 1_000_000:
                return f'{x/1_000_000:.1f}M'
            elif x >= 1_000:
                return f'{x/1_000:.0f}k'
            else:
                return f'{x:,.0f}'
        
        vmin = gdf[columna].min()
        vmax = gdf[columna].max()

        gdf.plot(
            column=columna, 
            cmap='RdYlGn_r',
            legend=True,
            legend_kwds={
                "label": self.titulo_activo,
                "shrink": 0.6,
                "pad": 0.02,
                "orientation": "horizontal",
                "format": FuncFormatter(formato_miles)
            },
            ax=ax,
            edgecolor='black',
            linewidth=0.3,
            missing_kwds={"color": "lightgray"},
            vmin=vmin,
            vmax=vmax
        )
        
        ax.set_title(f"{self.titulo_activo} por Estado", fontsize=16, fontweight="bold", pad=20)
        plt.tight_layout()
        return fig

    def _generar_figura_estatal(self, columna: str, tema: str, estado_clave: str):
        """Genera y retorna la figura del mapa estatal (no guarda archivo)"""
        nombre_estado = NOMBRES_ESTADOS.get(estado_clave, estado_clave)
        
        df = self._df_para_tema(tema)
        if df is None or columna not in df.columns:
            print(f"Error: Columna '{columna}' no encontrada en tema '{tema}'")
            return None
        if self.gdf_municipios is None:
            print("Error: No hay shapefile de municipios")
            return None

        df_estado = df[df["clave_estado"] == estado_clave].copy()
        df_estado = df_estado.loc[:, ~df_estado.columns.duplicated()]
        
        if 'clave_municipio' not in df_estado.columns:
            print("Error: 'clave_municipio' no es una columna")
            return None
        
        df_estado['clave_municipio'] = df_estado['clave_municipio'].astype(str).str.zfill(5)
        df_estado = df_estado.groupby('clave_municipio')[columna].sum().reset_index()
        
        gdf_mun_estado = self.gdf_municipios[self.gdf_municipios["CVEGEO"].str.startswith(estado_clave)].copy()
        
        if df_estado.empty or gdf_mun_estado.empty:
            print(f"Error: No hay datos para el estado {nombre_estado}")
            return None

        gdf_mun_estado["CVEGEO"] = gdf_mun_estado["CVEGEO"].astype(str).str.zfill(5)
        gdf = gdf_mun_estado.merge(df_estado, left_on="CVEGEO", right_on="clave_municipio", how="left")

        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_axis_off()
        
        from matplotlib.ticker import FuncFormatter
        def formato_miles(x, p):
            if x >= 1_000_000:
                return f'{x/1_000_000:.1f}M'
            elif x >= 1_000:
                return f'{x/1_000:.0f}k'
            else:
                return f'{x:,.0f}'
        
        gdf.plot(
            column=columna,
            cmap="YlOrRd",
            legend=True,
            legend_kwds={
                "label": self.titulo_activo,
                "shrink": 0.5,
                "pad": 0.02,
                "orientation": "horizontal",
                "format": FuncFormatter(formato_miles)
            },
            ax=ax,
            edgecolor="white",
            linewidth=0.3,
            missing_kwds={"color": "lightgray"}
        )
        
        ax.set_title(f"{self.titulo_activo} por Municipio - {nombre_estado}", fontsize=14, fontweight="bold", pad=14)
        plt.tight_layout()
        return fig

    def _df_para_tema(self, tema: str):
        return self.dfs.get(tema)

    def generar_mapa_nacional(self, columna: str, tema: str):
        """Genera mapa nacional y guarda archivo temporal PNG"""
        #print(f"\nGenerando mapa NACIONAL - Columna: {columna}, Tema: {tema}")
        
        fig = self._generar_figura_nacional(columna, tema)
        if fig is None:
            return None
        
        timestamp = int(time.time() * 1000)
        temp = os.path.join(os.path.dirname(__file__), f"_mapa_temp_{timestamp}.png")
        fig.savefig(temp, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        #print(f"Mapa nacional guardado temporalmente en: {temp}")
        return temp

    def generar_mapa_estatal(self, columna: str, tema: str, estado_clave: str):
        """Genera mapa estatal y guarda archivo temporal PNG"""
        nombre_estado = NOMBRES_ESTADOS.get(estado_clave, estado_clave)
        #print(f"\nGenerando mapa ESTATAL - Estado: {nombre_estado} ({estado_clave}), Columna: {columna}")
        
        fig = self._generar_figura_estatal(columna, tema, estado_clave)
        if fig is None:
            return None
        
        timestamp = int(time.time() * 1000)
        temp = os.path.join(os.path.dirname(__file__), f"_mapa_temp_{timestamp}.png")
        fig.savefig(temp, format="png", dpi=130, bbox_inches="tight")
        plt.close(fig)
        #print(f"Mapa estatal guardado temporalmente en: {temp}")
        return temp

    def generar_mapa(self):
        #print("\n" + "="*50)
        #print("Intentando generar mapa...")
        self._log_seleccion()
        
        if self.columna_activa is None or self.tema_activo is None:
            #print("No hay tema/columna seleccionada")
            return None
        if self.nivel_actual is None:
            #print("No hay nivel seleccionado")
            return None
        if self.nivel_actual == "estatal" and self.estado_seleccionado is None:
            #print("No hay estado seleccionado")
            return None
            
        if self.nivel_actual == "nacional":
            return self.generar_mapa_nacional(self.columna_activa, self.tema_activo)
        else:
            return self.generar_mapa_estatal(self.columna_activa, self.tema_activo, self.estado_seleccionado)

    # ── Sidebar ─────────────────────────────────────────────────────────────

    def _label(self, texto: str) -> str:
        return texto.replace("_", " ").title()

    def _build_sidebar(self) -> ft.Column:
        items = []

        for tema, tipos in SIDEBAR_TEMAS.items():
            tema_abierto = self._tema_abierto == tema

            def _on_tema(e, t=tema):
                print(f"\nClick en tema: {t}")
                self._tema_abierto = None if self._tema_abierto == t else t
                self._tipo_abierto = None
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

            for tipo, grupos in tipos.items():
                tipo_abierto = self._tipo_abierto == tipo

                def _on_tipo(e, tp=tipo):
                    print(f"\nClick en tipo: {tp}")
                    self._tipo_abierto = None if self._tipo_abierto == tp else tp
                    self._grupo_abierto = None
                    self._refrescar_sidebar()

                items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(tipo, size=13,
                                    color=ft.Colors.BLUE_600 if tipo_abierto else ft.Colors.GREY_700),
                            ft.Icon(ft.Icons.EXPAND_LESS if tipo_abierto else ft.Icons.EXPAND_MORE, size=16),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.only(left=20, right=12, top=7, bottom=7),
                        bgcolor=ft.Colors.BLUE_50 if tipo_abierto else "transparent",
                        border_radius=6,
                        on_click=_on_tipo,
                        ink=True,
                    )
                )

                if not tipo_abierto:
                    continue

                for grupo, columnas in grupos.items():
                    if not columnas:
                        continue
                    grupo_abierto = self._grupo_abierto == grupo

                    def _on_grupo(e, g=grupo):
                        print(f"\nClick en grupo: {g}")
                        self._grupo_abierto = None if self._grupo_abierto == g else g
                        self._refrescar_sidebar()

                    items.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(grupo, size=12, color=ft.Colors.GREY_800),
                                ft.Icon(ft.Icons.EXPAND_LESS if grupo_abierto else ft.Icons.EXPAND_MORE, size=14),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.only(left=32, right=12, top=5, bottom=5),
                            bgcolor=ft.Colors.GREY_100 if grupo_abierto else "transparent",
                            border_radius=5,
                            on_click=_on_grupo,
                            ink=True,
                        )
                    )

                    if not grupo_abierto:
                        continue

                    for col in columnas:
                        activa = col == self.columna_activa

                        def _on_col(e, c=col, tm=tema.lower(), tp=tipo.lower()):
                            print(f"\nClick en indicador: {self._label(c)}")
                            self.columna_activa = c
                            
                            tema_corregido = "poblacion" if tm == "población" else "salud" if tm == "salud" else "economicas"
                            tipo_corregido = "abs" if tp == "absoluto" else "rel"
                            
                            self.tema_activo = f"{tema_corregido}_{tipo_corregido}"
                            self.titulo_activo = self._label(c)
                            self._refrescar_sidebar()
                            if self.titulo_mapa_ref.current:
                                self.titulo_mapa_ref.current.value = self.titulo_activo
                            self._log_seleccion()
                            

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
            print("\nSeleccionado: Nacional")
            self.nivel_actual = "nacional"
            self._estados_abierto = False
            self._refrescar_sidebar()
            self._log_seleccion()
        
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
        
        def on_estatal(e):
            print("\nSeleccionado: Estatal")
            self.nivel_actual = "estatal"
            self._estados_abierto = not self._estados_abierto
            self._refrescar_sidebar()
            self._log_seleccion()
        
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
                    print(f"\nEstado seleccionado: {n}")
                    self.estado_seleccionado = c
                    self._estados_abierto = False
                    self._refrescar_sidebar()
                    self._log_seleccion()
                
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

    # ── Generar y mostrar ───────────────────────────────────────────────────
    def _generar_y_mostrar(self):
        print("\n" + "="*50)
        print("Click en 'Generar mapa'")
        
        # Verificar si los datos están cargados
        if self.dfs.get("poblacion_abs") is None:
            print("Datos aún no cargados. Espera un momento...")
            
            def cerrar_dialogo(dialog):
                dialog.open = False
                self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Cargando datos"),
                content=ft.Text("Los datos aún se están cargando.\nPor favor espera un momento y vuelve a intentar."),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            return
        
        self._log_seleccion()
            
        if self.columna_activa is None or self.tema_activo is None:
            print("No hay tema seleccionado. Por favor selecciona un indicador.")
            if self.placeholder_ref.current:
                self.placeholder_ref.current.visible = True
            if self.img_ref.current:
                self.img_ref.current.visible = False
            self.page.update()
            return
            
        if self.nivel_actual is None:
            print("No hay nivel seleccionado. Por favor selecciona Nacional o Estatal.")
            if self.placeholder_ref.current:
                self.placeholder_ref.current.visible = True
            self.page.update()
            return
            
        if self.nivel_actual == "estatal" and self.estado_seleccionado is None:
            print("No hay estado seleccionado. Por favor selecciona un estado.")
            if self.placeholder_ref.current:
                self.placeholder_ref.current.visible = True
            self.page.update()
            return

        print("Todos los criterios seleccionados. Generando mapa...")
        
        if self.spinner_ref.current:
            self.spinner_ref.current.visible = True
        if self.img_ref.current:
            self.img_ref.current.visible = False
        if self.placeholder_ref.current:
            self.placeholder_ref.current.visible = False
        if self.titulo_mapa_ref.current:
            self.titulo_mapa_ref.current.value = self.titulo_activo
        self.page.update()

        def _trabajo():
            path = self.generar_mapa()
            print(f"Path generado: {path}")
            if path and os.path.exists(path):
                print(f"Archivo existe: {path}")
            else:
                print(f"Archivo no existe: {path}")

            def _actualizar():
                if self.spinner_ref.current:
                    self.spinner_ref.current.visible = False
                if path:
                    print("Mapa generado correctamente, mostrando en pantalla.")
                    if self.img_ref.current:
                        self.img_ref.current.src = path
                        self.img_ref.current.visible = True
                    if self.placeholder_ref.current:
                        self.placeholder_ref.current.visible = False
                else:
                    print("Error al generar el mapa. Verifica los datos seleccionados.")
                    if self.placeholder_ref.current:
                        self.placeholder_ref.current.visible = True
                self.page.update()

            self.page.run_thread(_actualizar)

        threading.Thread(target=_trabajo, daemon=True).start()
    

    # ── Guardar ─────────────────────────────────────────────────────────────

    def _guardar_mapa(self, formato: str):
        if self.columna_activa is None or self.tema_activo is None:
            print("No se puede guardar: No hay tema seleccionado")
            return
        if self.nivel_actual is None:
            print("No se puede guardar: No hay nivel seleccionado")
            return
        if self.nivel_actual == "estatal" and self.estado_seleccionado is None:
            print("No se puede guardar: No hay estado seleccionado")
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_limpio = self.titulo_activo.replace(" ", "_").replace("/", "_")
        nombre = f"mapa_{nombre_limpio}_{timestamp}.{formato.lower()}"
        
        directorio = "C:/Mapas_SCINCE"
        os.makedirs(directorio, exist_ok=True)
        destino = os.path.join(directorio, nombre)

        print(f"\nGuardando mapa en: {destino}")
        
        if self.nivel_actual == "nacional":
            fig = self._generar_figura_nacional(self.columna_activa, self.tema_activo)
        else:
            fig = self._generar_figura_estatal(self.columna_activa, self.tema_activo, self.estado_seleccionado)

        if fig is None:
            print("Error: No se pudo generar el mapa para guardar")
            return

        dpi = 200 if formato in ("PNG", "JPG") else 150
        fig.savefig(destino, format=formato.lower(), dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        
        print(f"Mapa guardado exitosamente en: {destino}")
        
        def mostrar_mensaje():
            dialog = ft.AlertDialog(
                title=ft.Text("Mapa guardado"),
                content=ft.Text(f"Archivo guardado en:\n{destino}"),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog))
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        def cerrar_dialogo(dialog):
            dialog.open = False
            self.page.update()
        
        self.page.run_thread(mostrar_mensaje)

    def _dialogo_guardar(self, _):
        if self.columna_activa is None or self.tema_activo is None:
            print("No se puede guardar: No hay tema seleccionado")
            return
        if self.nivel_actual is None:
            print("No se puede guardar: No hay nivel seleccionado")
            return
            
        formato_sel = ft.Ref[ft.RadioGroup]()

        def confirmar(e):
            dlg.open = False
            self.page.update()
            fmt = formato_sel.current.value or "PNG"
            threading.Thread(target=self._guardar_mapa, args=(fmt,), daemon=True).start()

        def cancelar(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Guardar mapa"),
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

    # ── Build ────────────────────────────────────────────────────────────────

    def build(self):
        self._limpiar_temporales()
        self.page.clean()
        self.page.title = "SCINCE – Mapas"
        self.page.bgcolor = "#f5f5f5"
        self.page.padding = 0
        self.page.expand = True

        def volver(_):
            print("\nVolviendo al inicio...")
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from inicio import mostrar_sistema_principal
            mostrar_sistema_principal(self.page, self.usuario_data)

        topbar = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=volver, tooltip="Volver"),
                    ft.Text("Visualización de Mapas", size=18, weight="bold"),
                ]),
                ft.Text(self.usuario_data["nombre"], size=12, color="grey"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor="white",
            border_radius=ft.BorderRadius(0, 0, 15, 15),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200),
        )

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
                ft.ElevatedButton(
                    "Generar mapa",
                    icon=ft.Icons.MAP,
                    on_click=lambda _: self._generar_y_mostrar(),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                    width=180,
                ),
                ft.ElevatedButton(
                    "Guardar",
                    icon=ft.Icons.SAVE_ALT,
                    on_click=self._dialogo_guardar,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                    width=180,
                ),
            ], spacing=8, expand=True),
            width=280,
            padding=ft.padding.all(12),
            bgcolor="white",
            border_radius=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200),
        )

        area_mapa = ft.Container(
            content=ft.Stack([
                ft.Image(ref=self.img_ref, src=None, fit="contain", expand=True, visible=False),
                ft.Container(
                    ref=self.placeholder_ref,
                    content=ft.Column([
                        ft.Icon(ft.Icons.MAP_OUTLINED, size=80, color=ft.Colors.GREY_300),
                        ft.Text(
                            "Selecciona un tema",
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_400,
                            size=16,
                            weight="bold",
                        ),
                        ft.Text(
                            "Elige un indicador, selecciona nivel (Nacional/Estatal)\ny presiona 'Generar mapa'",
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

        titulo_mapa = ft.Text(
            ref=self.titulo_mapa_ref,
            value=self.titulo_activo,
            size=15,
            weight="bold",
            color=ft.Colors.BLUE_900,
        )

        contenido_columna = ft.Column(
            [ft.Row([titulo_mapa], alignment=ft.MainAxisAlignment.CENTER), area_mapa],
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

        def _on_datos_listos(exito):
            if not exito:
                print("No se encontraron algunos archivos de datos")
            else:
                print("\nTodos los datos cargados exitosamente")
                print("Esperando selección de usuario...")

        self.cargar_datos_async(_on_datos_listos)


def abrir_modulo_mapas(page: ft.Page, usuario_data: dict):
    ModuloMapas(page, usuario_data).build()