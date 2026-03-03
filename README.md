# Sistema de Autenticación

Interfaz gráfica para sistema de autenticación con métodos QR, llave USB y reconocimiento facial.

## Descripción
Aplicación desarrollada con Flet que proporciona una interfaz para:
- Inicio de sesión
- Registro de usuarios
- Verificación por QR
- Verificación por llave USB
- Reconocimiento facial

## Instalación
1. Clonar el repositorio
2. Instalar dependencias: `pip install flet`
3. Ejecutar: `python main.py`

## Estructura
- `main.py` - Interfaz principal
- `usb.py` - Script que genera llave usb
- `qro.py` - Script que genera codigo QR (mediante bluetooth)
- `face.oy` -Script que genera contraseña mediante face id
- `assets/` - Iconos y recursos gráficos
  - `QR.ico`
  - `USB.ico`
  - `FACE.ico`
- `cv_resources/` - Recursos graficos para camara
  - `marco_rostro.png`
- `database/` - esquema de base de datos
  - `consultas_estructura.sql`
  - `schema.sql`
  - `usuarios.sql`

## Requisitos
- Python 3.7+
- Flet

## Notas
18.02.26: Este proyecto actualmente implementa solo la interfaz de usuario. La lógica de autenticación y base de datos se integrará en futuras versiones.
Se implementó una primera versión que permite generar un QR y enviarlo por Bluetooth.

02.03.26: Los modulos de qr, facial y usb funcionan, se comenzarà con la base de datos.

