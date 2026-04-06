# analisis/utils/generar_graficos.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configurar matplotlib para usar UTF-8 y evitar notación científica
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.formatter.limits'] = (-6, 6)
plt.rcParams['axes.formatter.use_mathtext'] = False

def formatear_valor(valor):
    """Formatea un valor para mostrar en el gráfico (sin notación científica)"""
    if valor >= 1_000_000:
        return f'{valor/1_000_000:.1f}M'
    elif valor >= 1_000:
        return f'{valor/1_000:.0f}k'
    else:
        return f'{valor:,.0f}'

def preparar_datos_para_grafico(df, columna, nivel, estado_seleccionado=None, nombres_estados=None):
    """
    Prepara los datos según el nivel seleccionado
    """
    if df is None or columna not in df.columns:
        return None
    
    if nivel == "nacional":
        # Para nacional, agrupar por estado (todos los 32 estados)
        if "clave_estado" not in df.columns:
            return None
        
        # Sumar valores por estado
        datos = df.groupby("nombre_estado")[columna].sum().reset_index()
        datos.columns = ["nombre", "valor"]
        datos = datos.sort_values("valor", ascending=False)
        return datos
    
    else:
        # Para estatal, filtrar por estado y agrupar por municipio
        if estado_seleccionado is None:
            return None
        if "clave_estado" not in df.columns or "nombre_municipio" not in df.columns:
            return None
        
        datos = df[df["clave_estado"] == estado_seleccionado].copy()
        datos = datos.groupby("nombre_municipio")[columna].sum().reset_index()
        datos.columns = ["nombre", "valor"]
        datos = datos.sort_values("valor", ascending=False)
        return datos


def generar_grafico_barras(datos, titulo, xlabel="", ylabel=""):
    """Genera gráfico de barras - muestra todos los estados/municipios"""
    fig, ax = plt.subplots(figsize=(14, max(8, len(datos) * 0.3)))
    
    # Mostrar todos los datos (sin limitar)
    colores = plt.cm.Blues(np.linspace(0.4, 0.9, len(datos)))[::-1]
    bars = ax.bar(datos["nombre"], datos["valor"], color=colores, edgecolor='black', linewidth=0.5)
    
    # Agregar etiquetas de valores
    for bar, valor in zip(bars, datos["valor"]):
        texto = formatear_valor(valor)
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (bar.get_height()*0.01),
                texto, ha='center', va='bottom', fontsize=8, rotation=0)
    
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel if ylabel else titulo, fontsize=12)
    ax.set_title(titulo, fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def generar_grafico_boxplot(datos, titulo, ylabel=""):
    """Genera box plot"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    bp = ax.boxplot(datos["valor"], vert=True, patch_artist=True,
                    boxprops=dict(facecolor='lightblue', color='blue', linewidth=1.5),
                    whiskerprops=dict(color='blue', linewidth=1.5),
                    capprops=dict(color='blue', linewidth=1.5),
                    flierprops=dict(marker='o', markerfacecolor='red', markersize=6, alpha=0.5),
                    medianprops=dict(color='darkred', linewidth=2))
    
    # Estadísticas
    media = datos["valor"].mean()
    mediana = datos["valor"].median()
    
    ax.axhline(media, color='green', linestyle='--', linewidth=2, label=f'Media: {formatear_valor(media)}')
    ax.axhline(mediana, color='orange', linestyle='--', linewidth=2, label=f'Mediana: {formatear_valor(mediana)}')
    
    ax.set_ylabel(ylabel if ylabel else titulo, fontsize=12)
    ax.set_title(f"Distribución de {titulo}", fontsize=14, fontweight='bold')
    ax.set_xticklabels(['Datos'], fontsize=11)
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def generar_grafico_densidad(datos, titulo, xlabel=""):
    """Genera density plot (histograma + curva de densidad)"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    n, bins, patches = ax.hist(datos["valor"], bins=30, density=True, alpha=0.6, 
                                color='lightblue', edgecolor='black', label='Histograma')
    
    # Curva de densidad (KDE)
    from scipy.stats import gaussian_kde
    try:
        kde = gaussian_kde(datos["valor"])
        x_range = np.linspace(datos["valor"].min(), datos["valor"].max(), 200)
        ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='Densidad')
    except:
        pass
    
    media = datos["valor"].mean()
    mediana = datos["valor"].median()
    ax.axvline(media, color='green', linestyle='--', linewidth=2, label=f'Media: {formatear_valor(media)}')
    ax.axvline(mediana, color='orange', linestyle='--', linewidth=2, label=f'Mediana: {formatear_valor(mediana)}')
    
    ax.set_xlabel(xlabel if xlabel else titulo, fontsize=12)
    ax.set_ylabel("Densidad", fontsize=12)
    ax.set_title(f"Densidad de {titulo}", fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(axis='both', alpha=0.3)
    
    plt.tight_layout()
    return fig


def generar_grafico_porcentaje(datos, titulo, xlabel=""):
    """Genera gráfico de barras de porcentaje (todos los datos normalizados a 100%)"""
    fig, ax = plt.subplots(figsize=(14, max(8, len(datos) * 0.3)))
    
    total = datos["valor"].sum()
    porcentajes = (datos["valor"] / total) * 100
    
    colores = plt.cm.Greens(np.linspace(0.4, 0.9, len(datos)))[::-1]
    bars = ax.bar(datos["nombre"], porcentajes, color=colores, edgecolor='black', linewidth=0.5)
    
    for bar, pct in zip(bars, porcentajes):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    ax.set_ylabel("Porcentaje (%)", fontsize=12)
    ax.set_title(f"Distribución porcentual de {titulo}", fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def generar_grafico_histograma(datos, titulo, xlabel=""):
    """Genera histograma destacando la media"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    n, bins, patches = ax.hist(datos["valor"], bins=20, edgecolor='black', alpha=0.7, color='lightblue')
    
    # Destacar barras cerca de la media
    media = datos["valor"].mean()
    for patch, bin_edge in zip(patches, bins[:-1]):
        if abs(bin_edge - media) < (bins[1] - bins[0]) * 2:
            patch.set_facecolor('orange')
            patch.set_edgecolor('darkorange')
            patch.set_linewidth(1.5)
    
    mediana = datos["valor"].median()
    ax.axvline(media, color='red', linestyle='--', linewidth=2, label=f'Media: {formatear_valor(media)}')
    ax.axvline(mediana, color='green', linestyle='--', linewidth=2, label=f'Mediana: {formatear_valor(mediana)}')
    
    ax.set_xlabel(xlabel if xlabel else titulo, fontsize=12)
    ax.set_ylabel("Frecuencia", fontsize=12)
    ax.set_title(f"Histograma de {titulo}", fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(axis='both', alpha=0.3)
    
    plt.tight_layout()
    return fig


def generar_grafico_lineas(datos, titulo, ylabel=""):
    """Genera gráfico de líneas (tendencia) - muestra todos los datos ordenados"""
    fig, ax = plt.subplots(figsize=(14, max(8, len(datos) * 0.2)))
    
    # Ordenar por valor
    datos_ordenados = datos.sort_values("valor")
    
    ax.plot(range(len(datos_ordenados)), datos_ordenados["valor"], 
            marker='o', linewidth=2.5, markersize=6, color='blue', label=titulo)
    
    ax.fill_between(range(len(datos_ordenados)), 0, datos_ordenados["valor"], alpha=0.3, color='lightblue')
    
    # Marcar puntos máximos y mínimos
    max_idx = datos_ordenados["valor"].idxmax()
    min_idx = datos_ordenados["valor"].idxmin()
    ax.plot(datos_ordenados.index.get_loc(max_idx), datos_ordenados.loc[max_idx, "valor"], 
            'ro', markersize=10, label='Máximo')
    ax.plot(datos_ordenados.index.get_loc(min_idx), datos_ordenados.loc[min_idx, "valor"], 
            'go', markersize=10, label='Mínimo')
    
    # Etiquetas de valores en puntos extremos
    ax.text(datos_ordenados.index.get_loc(max_idx), datos_ordenados.loc[max_idx, "valor"],
            f' {formatear_valor(datos_ordenados.loc[max_idx, "valor"])}', 
            va='bottom', fontsize=9, fontweight='bold')
    ax.text(datos_ordenados.index.get_loc(min_idx), datos_ordenados.loc[min_idx, "valor"],
            f' {formatear_valor(datos_ordenados.loc[min_idx, "valor"])}', 
            va='top', fontsize=9, fontweight='bold')
    
    ax.set_xlabel("Índice (ordenado por valor)", fontsize=12)
    ax.set_ylabel(ylabel if ylabel else titulo, fontsize=12)
    ax.set_title(f"Tendencia de {titulo}", fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def generar_grafico_segun_tipo(tipo, datos, titulo, xlabel="", ylabel=""):
    """
    Genera gráfico según el tipo seleccionado
    """
    if datos is None or len(datos) == 0:
        return None
    
    if tipo == "bar_chart":
        return generar_grafico_barras(datos, titulo, xlabel, ylabel)
    elif tipo == "box_plot":
        return generar_grafico_boxplot(datos, titulo, ylabel)
    elif tipo == "density":
        return generar_grafico_densidad(datos, titulo, xlabel)
    elif tipo == "percentage":
        return generar_grafico_porcentaje(datos, titulo, xlabel)
    elif tipo == "histogram":
        return generar_grafico_histograma(datos, titulo, xlabel)
    elif tipo == "line_chart":
        return generar_grafico_lineas(datos, titulo, ylabel)
    else:
        return None