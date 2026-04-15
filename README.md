# Sistema SCINCE - Análisis de datos demográficos

Sistema completo que integra autenticación multifactor (QR, USB, facial) y análisis de datos del Censo INEGI 2020 con visualización de mapas, gráficos y reportes exportables.

## Descripción General

SCINCE consta de dos grandes módulos:

### 1. Autenticación
- Registro de usuarios
- Inicio de sesión con contraseña
- Segundo factor de verificación:
  - Código QR enviado por Bluetooth
  - Llave USB (par de claves RSA)
  - Reconocimiento facial (OpenCV)

### 2. Análisis de datos (módulo principal)
- **Mapas**: Visualización geográfica por estado o municipio
- **Gráficos**: 6 tipos (barras, cajas, densidad, porcentaje, histograma, líneas)
- **Reportes**: Tablas comparativas con múltiples indicadores
- Exportación a PNG, PDF, JPG, Excel
- Datos del Censo INEGI 2020 (Población, Economía, Salud)

## Requisitos del Sistema

- Python 3.11 (recomendado) - **No usar Python 3.13**
- Windows 10/11 (recomendado para reconocimiento facial y USB)
- Cámara (para QR y facial)
- Bluetooth (para envío de QR)
- 4GB de RAM mínimo
- 2GB de espacio en disco (para datos y shapefiles)

## Instalación

### 1. Clonar el repositorio
git clone https://github.com/pablo27exe/Sistema

### 2. Instalar dependencias
pip install -r requirements.txt

### 3.Configurar variables de entorno
Crear archivo .env en la raíz con:

- DB_HOST=localhost
- DB_PORT=5432
- DB_NAME=scince_db
- DB_USER=postgres
- DB_PASSWORD=tu_contraseña

### 4. Datos externos (descarga manual)
Los siguientes archivos NO están incluidos en el repositorio por su tamaño. Descargarlos desde: https://drive.google.com/drive/folders/1VNwc3fLZmCRWZ5Bzjlmh2PrLi0EMCG9m?usp=sharing

CSVs del INEGI (colocar en analisis/datos/)
- PoblacionABS.csv
- PoblacionREL.csv
- EconomiaABS.csv
- EconomiaREL.csv
- SaludABS.csv
- SaludREL.csv

Shapefiles (colocar en analisis/shapefiles/)
Carpeta con subcarpetas 01_aguascalientes/, 02_bajacalifornia/, etc.

Cada subcarpeta debe contener:

- XX_estado_ent.shp (estados)
- XX_estado_mun.shp (municipios)

### 5. Base de datos PostgreSQL
Ejecutar los scripts en database/
Especialmente el que permite crearla

## Estructura

### Autenticación
- `main.py` - Pantalla de login (punto de entrada del programa)
- `usuarios.py` - Operaciones CRUD para usuarios
- `credenciales.py` - Gestión de contraseñas
- `segundo_metodo.py` - Consultas para segundo factor
- `metodos_segundo_factor.py` - Inserción de métodos de verificación
- `usb.py` - Generación de llave USB (RSA)
- `qro.py` - Generación de código QR enviado por Bluetooth
- `face.py` - Reconocimiento facial con OpenCV
- `auth/assets/` - Iconos y recursos gráficos
  - `QR.ico`
  - `USB.ico`
  - `FACE.ico`
- `cv_resources/` - Recursos gráficos para cámara
  - `marco_rostro.png`

### Análisis de datos
- `analisis/inicio.py` - Pantalla principal después del login
- `analisis/modulos/mapas.py` - Visualización de mapas coropléticos
- `analisis/modulos/graficos.py` - Generación de gráficos (barras, cajas, densidad, porcentaje, histograma, líneas)
- `analisis/modulos/reportes.py` - Tablas comparativas y exportación (Excel, PDF)
- `analisis/utils/datos.py` - Carga de CSVs y shapefiles
- `analisis/utils/mapeos.py` - Diccionarios de traducción de columnas
- `analisis/utils/generar_graficos.py` - Funciones de generación de gráficos

### Base de datos
- `database/` - Scripts SQL
  - `schema.sql`
  - `usuarios.sql`
  - `consultas_estructura.sql`
  - `left_join.sql`
  - `registros_incompletos.sql`
  - `verificacion_separada.sql`

### Archivos ignorados (no incluidos en repo)
- `analisis/datos/` - CSVs del INEGI (Población, Economía, Salud)
- `analisis/shapefiles/` - Shapefiles del INEGI (estados y municipios)
- `facial_data/` - Modelos entrenados de reconocimiento facial (archivos .yml y .pkl)
- `.env` - Variables de entorno (base de datos)

### Archivos generados por el sistema
- `C:/Mapas_SCINCE/` - Mapas exportados (PNG, PDF, JPG)
- `C:/Graficos_SCINCE/` - Gráficos exportados (PNG, PDF, JPG)
- `C:/Reportes_SCINCE/` - Reportes exportados (Excel, PDF)
- `analisis/modulos/_mapa_temp_*.png` - Archivos temporales de mapas
- `analisis/modulos/_grafico_temp_*.png` - Archivos temporales de gráficos

### Configuración
- `requirements.txt` - Dependencias del proyecto
- `README.md` - Documentación principal
- `.gitignore` - Archivos ignorados por Git