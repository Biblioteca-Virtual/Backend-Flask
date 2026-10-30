-- ======================================================================
-- Migración 010: cada usuario tiene su propia biblioteca.
--   - libros.usuario_id: dueño del libro (los existentes pasan al primer
--     usuario llamado Maximo Massut, o al de menor id si no existe).
--   - Se quitan isbn, anio_publicacion y cantidad (copias físicas).
--   - Se agrega ubicacion (fisico / kindle / web) y url_lectura para 'web'.
-- Es idempotente para poder ejecutarla también sobre una base recién inicializada.
-- ======================================================================
BEGIN;

ALTER TABLE libros
    ADD COLUMN IF NOT EXISTS usuario_id INTEGER,
    ADD COLUMN IF NOT EXISTS ubicacion VARCHAR(10) NOT NULL DEFAULT 'fisico',
    ADD COLUMN IF NOT EXISTS url_lectura VARCHAR(500);

UPDATE libros
SET usuario_id = COALESCE(
    (SELECT id FROM usuarios WHERE nombre = 'Maximo' AND apellido = 'Massut' ORDER BY id LIMIT 1),
    (SELECT MIN(id) FROM usuarios)
)
WHERE usuario_id IS NULL;

-- Sin usuarios no hay a quién asignar los libros de demostración.
DELETE FROM libros WHERE usuario_id IS NULL;

ALTER TABLE libros
    ALTER COLUMN usuario_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_libro_usuario' AND conrelid = 'libros'::regclass
    ) THEN
        ALTER TABLE libros
            ADD CONSTRAINT fk_libro_usuario
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_ubicacion' AND conrelid = 'libros'::regclass
    ) THEN
        ALTER TABLE libros
            ADD CONSTRAINT check_ubicacion
            CHECK (ubicacion IN ('fisico', 'kindle', 'web'));
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_libros_usuario ON libros(usuario_id);

ALTER TABLE libros
    DROP CONSTRAINT IF EXISTS check_anio_publicacion,
    DROP CONSTRAINT IF EXISTS check_cantidad,
    DROP COLUMN IF EXISTS isbn,
    DROP COLUMN IF EXISTS anio_publicacion,
    DROP COLUMN IF EXISTS cantidad;

COMMIT;
