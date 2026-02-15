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
- `assets/` - Iconos y recursos gráficos
  - `QR.ico`
  - `USB.ico`
  - `FACE.ico`

## Requisitos
- Python 3.7+
- Flet

## Notas
Este proyecto actualmente implementa solo la interfaz de usuario. La lógica de autenticación y base de datos se integrará en futuras versiones.