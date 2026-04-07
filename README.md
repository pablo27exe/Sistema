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

DB_HOST=localhost
DB_PORT=5432
DB_NAME=scince_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña

### 4. Datos externos (descarga manual)
Los siguientes archivos NO están incluidos en el repositorio por su tamaño. Descargarlos desde:

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

## Estructura del proyecto
scince/
├── analisis/                 # Módulo principal de análisis
│   ├── inicio.py            # Pantalla principal después del login
│   ├── datos/               # CSVs (ignorado por Git)
│   ├── shapefiles/          # Shapefiles (ignorado por Git)
│   ├── modulos/
│   │   ├── mapas.py
│   │   ├── graficos.py
│   │   └── reportes.py
│   └── utils/
│       ├── datos.py
│       ├── mapeos.py
│       └── generar_graficos.py
├── auth/                     # Módulo de autenticación
│   ├── usuarios.py
│   ├── credenciales.py
│   ├── segundo_metodo.py
│   ├── qro.py
│   ├── usb.py
│   ├── face.py
│   └── assets/              # Iconos
├── database/                 # Scripts SQL
├── facial_data/             # Modelos faciales (ignorado)
├── .env                     # Variables de entorno (ignorado)
├── requirements.txt
├── README.md
└── Main.py               #Pantalla de login (aquí se ejecuta el programa)
