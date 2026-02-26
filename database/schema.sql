-- Extensión para generar UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabla 1: Usuarios
CREATE TABLE usuarios (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre           VARCHAR(100) NOT NULL,
    nombre_usuario   VARCHAR(50)  NOT NULL UNIQUE,
    fecha_creacion   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Tabla 2: Credenciales
CREATE TABLE credenciales (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id       UUID        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    hash_contrasena  TEXT        NOT NULL,
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_credencial_usuario UNIQUE (usuario_id)
);

-- Enum para los tipos de segundo factor
CREATE TYPE tipo_segundo_factor AS ENUM ('qr', 'facial', 'usb');

-- Tabla 3: Métodos de segundo factor
CREATE TABLE metodos_segundo_factor (
    id            UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id    UUID                NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo          tipo_segundo_factor NOT NULL,
    activo        BOOLEAN             NOT NULL DEFAULT TRUE,
    dato_factor   TEXT,
    registrado_en TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

-- Índice para consultar la llave USB activa de un usuario rápidamente
CREATE UNIQUE INDEX uq_usb_activo_por_usuario
    ON metodos_segundo_factor (usuario_id)
    WHERE tipo = 'usb' AND activo = TRUE;