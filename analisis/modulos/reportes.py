# analisis/modulos/reportes.py

import flet as ft
import pandas as pd
import os
import sys
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.datos import cargar_csv_poblacion, cargar_csv_economicas, cargar_csv_salud, NOMBRES_ESTADOS
from utils.mapeos import (
    MAPEO_POBLACION_ABS, MAPEO_POBLACION_REL,
    MAPEO_ECONOMICAS_ABS, MAPEO_ECONOMICAS_REL,
    MAPEO_SALUD_ABS, MAPEO_SALUD_REL
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

GRUPOS_SALUD_REL = {
    "Afiliación": list(MAPEO_SALUD_REL.values()),
}

SIDEBAR_TEMAS = {
    "Población": {
        "Absoluto": GRUPOS_POBLACION_ABS,
        "Relativo": GRUPOS_POBLACION_REL,
    },
    "Salud": {
        "Absoluto": GRUPOS_SALUD_ABS,
        "Relativo": GRUPOS_SALUD_REL,
    },
    "Economía": {
        "Absoluto": GRUPOS_ECONOMICAS_ABS,
        "Relativo": GRUPOS_ECONOMICAS_REL,
    },
}


# ── Módulo principal ────────────────────────────────────────────────────────

class ModuloReportes:
    def __init__(self, page: ft.Page, usuario_data: dict):
        self.page = page
        self.usuario_data = usuario_data

        # Datos
        self.dfs = {}

        # Estado de la UI
        self.nivel_actual = None
        self.estado_seleccionado = None
        self.indicadores_seleccionados = []  # Lista de (tema, tipo, columna, titulo)
        
        # Referencias
        self.tabla_ref = ft.Ref[ft.Column]()
        self.sidebar_col_ref = ft.Ref[ft.Column]()
        self.lista_indicadores_ref = ft.Ref[ft.Column]()
        
        # Estado del árbol sidebar
        self._tema_abierto = None
        self._tipo_abierto = None
        self._grupo_abierto = None
        
        # Estado del selector de nivel
        self._estados_abierto = False

    # ── Carga de datos ──────────────────────────────────────────────────────

    def _cargar_datos_thread(self, on_done):
        try:
            print("\nCargando datos para reportes...")
            self.dfs["poblacion_abs"] = cargar_csv_poblacion("abs")
            self.dfs["poblacion_rel"] = cargar_csv_poblacion("rel")
            self.dfs["economicas_abs"] = cargar_csv_economicas("abs")
            self.dfs["economicas_rel"] = cargar_csv_economicas("rel")
            self.dfs["salud_abs"] = cargar_csv_salud("abs")
            self.dfs["salud_rel"] = cargar_csv_salud("rel")
            exito = self.dfs["poblacion_abs"] is not None
        except Exception as e:
            print(f"Error cargando datos: {e}")
            exito = False
        on_done(exito)

    def cargar_datos_async(self, on_done):
        threading.Thread(target=self._cargar_datos_thread, args=(on_done,), daemon=True).start()

    def _df_para_tema(self, tema: str):
        return self.dfs.get(tema)

    # ── Sidebar ─────────────────────────────────────────────────────────────

    def _label(self, texto: str) -> str:
        return texto.replace("_", " ").title()

    def _build_sidebar(self) -> ft.Column:
        items = []

        for tema, tipos in SIDEBAR_TEMAS.items():
            tema_abierto = self._tema_abierto == tema
            
            # Definir tema_key sin acentos
            if tema == "Población":
                tema_key = "poblacion"
            elif tema == "Salud":
                tema_key = "salud"
            else:
                tema_key = "economicas"

            def _on_tema(e, t=tema):
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
                tipo_key = "abs" if tipo == "Absoluto" else "rel"

                def _on_tipo(e, tp=tipo):
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
                        self._grupo_abierto = None if self._grupo_abierto == g else g
                        self._refrescar_sidebar()

                    items.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(grupo, size=12,
                                        color=ft.Colors.GREY_800),
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
                        label = self._label(col)
                        
                        def _on_col(e, c=col, tk=tema_key, tp=tipo_key, lbl=label):
                            # Verificar si ya está seleccionado
                            for item in self.indicadores_seleccionados:
                                if item["columna"] == c and item["tema"] == tk and item["tipo"] == tp:
                                    return
                            # Agregar indicador
                            self.indicadores_seleccionados.append({
                                "tema": tk,
                                "tipo": tp,
                                "columna": c,
                                "titulo": lbl
                            })
                            self._refrescar_sidebar()
                            self._actualizar_lista_indicadores()
                            self._actualizar_tabla()

                        items.append(
                            ft.Container(
                                content=ft.Text(label, size=11,
                                                color=ft.Colors.BLUE_700,
                                                weight="normal",
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                padding=ft.padding.only(left=44, right=8, top=4, bottom=4),
                                bgcolor=ft.Colors.BLUE_50,
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
            self._actualizar_tabla()

        def on_estatal(e):
            self.nivel_actual = "estatal"
            self._estados_abierto = not self._estados_abierto
            self._refrescar_sidebar()
            self._actualizar_tabla()

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
                    self._actualizar_tabla()

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

    def _actualizar_lista_indicadores(self):
        """Actualiza la lista visual de indicadores seleccionados"""
        if self.lista_indicadores_ref.current is None:
            return
        
        items = []
        for i, ind in enumerate(self.indicadores_seleccionados):
            def eliminar(e, idx=i):
                self.indicadores_seleccionados.pop(idx)
                self._actualizar_lista_indicadores()
                self._actualizar_tabla()
            
            items.append(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN_700),
                    ft.Text(f"{ind['titulo']}", size=12, expand=True),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_size=16, on_click=eliminar),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
        
        if not items:
            items.append(ft.Text("No hay indicadores seleccionados", size=12, color=ft.Colors.GREY_500))
        
        self.lista_indicadores_ref.current.controls = items
        self.page.update()

    def _formatear_valor(self, valor, es_relativo=False):
        """Formatea un valor para mostrar en la tabla"""
        if valor is None or pd.isna(valor):
            return "N/A"
        if isinstance(valor, (int, float)):
            if es_relativo:
                # Datos relativos (porcentajes)
                return f'{valor:.1f}%'
            else:
                # Datos absolutos: valores completos con separadores de miles
                return f'{valor:,.0f}'
        return str(valor)

    def _obtener_datos_tabla(self):
        """Obtiene los datos para la tabla según nivel e indicadores seleccionados"""
        if not self.indicadores_seleccionados:
            return None, None, None
        
        tipos_columnas = {}
        
        if self.nivel_actual == "nacional":
            # Obtener datos a nivel nacional (por estado)
            df_principal = None
            
            for ind in self.indicadores_seleccionados:
                es_relativo = ind["tipo"] == "rel"
                tipos_columnas[ind["columna"]] = es_relativo
                df = self._df_para_tema(f"{ind['tema']}_{ind['tipo']}")
                if df is None or ind["columna"] not in df.columns:
                    continue
                
                # Agrupar por estado
                df_agg = df.groupby("nombre_estado")[ind["columna"]].sum().reset_index()
                df_agg.columns = ["nombre", ind["columna"]]
                
                if df_principal is None:
                    df_principal = df_agg
                else:
                    df_principal = df_principal.merge(df_agg, on="nombre", how="outer")
            
            if df_principal is not None:
                df_principal = df_principal.fillna(0)
                columnas = ["nombre"] + [ind["columna"] for ind in self.indicadores_seleccionados]
                titulos = ["Estado"] + [ind["titulo"] for ind in self.indicadores_seleccionados]
                return df_principal[columnas], titulos, tipos_columnas
        else:
            # Nivel estatal
            if self.estado_seleccionado is None:
                return None, None, None
            
            df_principal = None
            
            for ind in self.indicadores_seleccionados:
                es_relativo = ind["tipo"] == "rel"
                tipos_columnas[ind["columna"]] = es_relativo
                df = self._df_para_tema(f"{ind['tema']}_{ind['tipo']}")
                if df is None or ind["columna"] not in df.columns:
                    continue
                
                # Filtrar por estado y agrupar por municipio
                df_estado = df[df["clave_estado"] == self.estado_seleccionado].copy()
                df_agg = df_estado.groupby("nombre_municipio")[ind["columna"]].sum().reset_index()
                df_agg.columns = ["nombre", ind["columna"]]
                
                if df_principal is None:
                    df_principal = df_agg
                else:
                    df_principal = df_principal.merge(df_agg, on="nombre", how="outer")
            
            if df_principal is not None:
                df_principal = df_principal.fillna(0)
                df_principal = df_principal.sort_values(df_principal.columns[1], ascending=False)
                columnas = ["nombre"] + [ind["columna"] for ind in self.indicadores_seleccionados]
                titulos = ["Municipio"] + [ind["titulo"] for ind in self.indicadores_seleccionados]
                return df_principal[columnas], titulos, tipos_columnas
        
        return None, None, None

    def _actualizar_tabla(self):
        """Actualiza la tabla con los datos actuales"""
        if self.tabla_ref.current is None:
            return
        
        datos, titulos, _ = self._obtener_datos_tabla()
        
        if datos is None or len(datos) == 0:
            self.tabla_ref.current.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.TABLE_CHART, size=80, color=ft.Colors.GREY_300),
                        ft.Text("Selecciona indicadores y nivel", size=16, color=ft.Colors.GREY_500),
                        ft.Text("Haz clic en cualquier indicador del sidebar para agregarlo", size=12, color=ft.Colors.GREY_400),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    expand=True,
                )
            ]
            self.page.update()
            return
        
        # Crear tabla
        rows = []
        for _, row in datos.iterrows():
            cells = []
            for col in datos.columns:
                if col == "nombre":
                    cells.append(ft.DataCell(ft.Text(str(row[col]), size=11)))
                else:
                    cells.append(ft.DataCell(ft.Text(self._formatear_valor(row[col]), size=11)))
            rows.append(ft.DataRow(cells=cells))
        
        # Columnas de la tabla
        columns = []
        for titulo in titulos:
            columns.append(ft.DataColumn(ft.Text(titulo, size=12, weight="bold")))
        
        # Scroll vertical para la tabla
        tabla = ft.Container(
            content=ft.Column([
                ft.DataTable(
                    columns=columns,
                    rows=rows,
                    heading_row_color=ft.Colors.BLUE_50,
                    horizontal_lines=ft.border.BorderSide(0.5, ft.Colors.GREY_300),
                    column_spacing=20,
                    width=float("inf"),
                )
            ], scroll=ft.ScrollMode.AUTO, height=500),
            expand=True,
        )
        
        self.tabla_ref.current.controls = [tabla]
        self.page.update()

    def _exportar_excel(self, e):
        """Exporta la tabla a Excel"""
        datos, titulos, _ = self._obtener_datos_tabla()
        if datos is None or len(datos) == 0:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"reporte_{timestamp}.xlsx"
        directorio = "C:/Reportes_SCINCE"
        os.makedirs(directorio, exist_ok=True)
        destino = os.path.join(directorio, nombre)
        
        # Renombrar columnas para el Excel
        df_export = datos.copy()
        df_export.columns = titulos
        
        df_export.to_excel(destino, index=False, sheet_name="Reporte")
        
        def mostrar_mensaje():
            def cerrar_dialogo(dialog):
                dialog.open = False
                self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("✅ Reporte exportado"),
                content=ft.Text(f"Archivo guardado en:\n{destino}"),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog))
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        
        self.page.run_thread(mostrar_mensaje)

    def _exportar_pdf(self, e):
        """Exporta la tabla a PDF usando matplotlib con paginación (20 filas por página)"""
        datos, titulos, tipos_columnas = self._obtener_datos_tabla()
        if datos is None or len(datos) == 0:
            return
        
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"reporte_{timestamp}.pdf"
        directorio = "C:/Reportes_SCINCE"
        os.makedirs(directorio, exist_ok=True)
        destino = os.path.join(directorio, nombre)
        
        # Configuración de paginación
        FILAS_POR_PAGINA = 20
        n_total_filas = len(datos)
        n_paginas = (n_total_filas + FILAS_POR_PAGINA - 1) // FILAS_POR_PAGINA
        
        pdf = PdfPages(destino)
        
        for pagina in range(n_paginas):
            inicio = pagina * FILAS_POR_PAGINA
            fin = min(inicio + FILAS_POR_PAGINA, n_total_filas)
            datos_pagina = datos.iloc[inicio:fin]
            
            # Calcular altura según filas de esta página (+1 por encabezado)
            n_filas_pagina = len(datos_pagina) + 1
            altura = max(6, n_filas_pagina * 0.35)
            ancho = 16
            
            fig, ax = plt.subplots(figsize=(ancho, altura))
            ax.axis('off')
            
            # Preparar datos para la tabla
            table_data = [titulos]
            for _, row in datos_pagina.iterrows():
                row_data = []
                for col in datos_pagina.columns:
                    if col == "nombre":
                        row_data.append(str(row[col]))
                    else:
                        es_relativo = tipos_columnas.get(col, False)
                        row_data.append(self._formatear_valor(row[col], es_relativo))
                table_data.append(row_data)
            
            # Crear tabla
            table = ax.table(cellText=table_data, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            
            # Ajustar tamaño de fuente
            if n_filas_pagina > 20:
                table.set_fontsize(6)
            elif n_filas_pagina > 15:
                table.set_fontsize(7)
            else:
                table.set_fontsize(8)
            
            table.scale(1, 1.2)
            
            # Colorear encabezado
            for j in range(len(titulos)):
                table[(0, j)].set_facecolor('#4472C4')
                table[(0, j)].set_text_props(weight='bold', color='white')
            
            # Títulos
            titulo_principal = f"Reporte SCINCE"
            subtitulo = f"Página {pagina + 1} de {n_paginas}"
            fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Posicionar títulos
            plt.suptitle(titulo_principal, fontsize=14, fontweight='bold', y=0.98)
            plt.title(f"{subtitulo} | Generado: {fecha}", fontsize=9, y=0.95, alpha=0.7)
            
            # Ajustar márgenes (más compacto)
            plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.05)
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        pdf.close()
        
        def mostrar_mensaje():
            def cerrar_dialogo(dialog):
                dialog.open = False
                self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("✅ Reporte exportado"),
                content=ft.Text(f"Archivo guardado en:\n{destino}\n\nTotal de páginas: {n_paginas}"),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogo(dialog))
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        
        self.page.run_thread(mostrar_mensaje)

    def _eliminar_ultimo(self, e):
        """Elimina el último indicador seleccionado"""
        if self.indicadores_seleccionados:
            self.indicadores_seleccionados.pop()
            self._actualizar_lista_indicadores()
            self._actualizar_tabla()

    def _limpiar_todos(self, e):
        """Elimina todos los indicadores seleccionados"""
        self.indicadores_seleccionados = []
        self._actualizar_lista_indicadores()
        self._actualizar_tabla()

    # ── Build ────────────────────────────────────────────────────────────────

    def build(self):
        self.page.clean()
        self.page.title = "Reportes"
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
                    ft.Text("Reportes", size=18, weight="bold"),
                ]),
                ft.Text(self.usuario_data["nombre"], size=12, color="grey"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor="white",
            border_radius=ft.BorderRadius(0, 0, 15, 15),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200),
        )

        # Botones de acción
        btn_agregar = ft.ElevatedButton(
            "Añadir indicador",
            icon=ft.Icons.ADD,
            disabled=True,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
        )
        
        btn_eliminar_ultimo = ft.ElevatedButton(
            "Eliminar último",
            icon=ft.Icons.REMOVE,
            on_click=self._eliminar_ultimo,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE),
        )
        
        btn_limpiar = ft.ElevatedButton(
            "Limpiar todo",
            icon=ft.Icons.CLEAR,
            on_click=self._limpiar_todos,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )
        
        btn_excel = ft.ElevatedButton(
            "Exportar Excel",
            icon=ft.Icons.TABLE_CHART,
            on_click=self._exportar_excel,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
        )
        
        btn_pdf = ft.ElevatedButton(
            "Exportar PDF",
            icon=ft.Icons.PICTURE_AS_PDF,
            on_click=self._exportar_pdf,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )

        # Barra de botones
        botones_accion = ft.Container(
            content=ft.Row(
                [btn_eliminar_ultimo, btn_limpiar, btn_excel, btn_pdf],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor="white",
            border_radius=15,
            margin=ft.margin.only(bottom=10),
        )

        # Lista de indicadores seleccionados
        lista_indicadores = ft.Container(
            content=ft.Column([
                ft.Text("Indicadores seleccionados:", size=13, weight="bold"),
                ft.Column(ref=self.lista_indicadores_ref, spacing=5),
            ]),
            padding=10,
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            margin=ft.margin.only(bottom=10),
        )

        # Área de la tabla
        area_tabla = ft.Container(
            content=ft.Column(ref=self.tabla_ref, expand=True),
            expand=True,
            bgcolor="white",
            border_radius=15,
            padding=10,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_200),
        )

        # Sidebar
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

        # Contenido principal
        contenido_columna = ft.Column(
            [lista_indicadores, botones_accion, area_tabla],
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
                print("❌ No se encontraron algunos archivos de datos")
            else:
                print("\n✅ Todos los datos cargados exitosamente")
                print("📌 Esperando selección de usuario...")
                self._actualizar_lista_indicadores()

        self.cargar_datos_async(_on_datos_listos)


def abrir_modulo_reportes(page: ft.Page, usuario_data: dict):
    ModuloReportes(page, usuario_data).build()