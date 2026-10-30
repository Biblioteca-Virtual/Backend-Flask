-- ======================================================================
-- Migración 009: colecciones de libros por usuario.
-- Es idempotente para poder ejecutarla también sobre una base recién inicializada.
-- ======================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS colecciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_coleccion_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_coleccion_usuario_nombre
        UNIQUE (usuario_id, nombre)
);

CREATE TABLE IF NOT EXISTS colecciones_libros (
    coleccion_id INTEGER NOT NULL,
    libro_id INTEGER NOT NULL,

    PRIMARY KEY (coleccion_id, libro_id),

    CONSTRAINT fk_coleccion_libro_coleccion
        FOREIGN KEY (coleccion_id)
        REFERENCES colecciones(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_coleccion_libro_libro
        FOREIGN KEY (libro_id)
        REFERENCES libros(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_colecciones_usuario
    ON colecciones(usuario_id);

COMMIT;
