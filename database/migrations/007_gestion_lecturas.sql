-- Migración de la issue #7: seguimiento de lecturas.
-- Es idempotente para poder ejecutarla también sobre una base recién inicializada.
BEGIN;

ALTER TABLE prestamos
    ADD COLUMN IF NOT EXISTS fecha_actualizacion TIMESTAMP,
    ADD COLUMN IF NOT EXISTS progreso INTEGER;

UPDATE prestamos
SET fecha_actualizacion = CURRENT_TIMESTAMP
WHERE fecha_actualizacion IS NULL;

UPDATE prestamos
SET progreso = 0
WHERE progreso IS NULL;

ALTER TABLE prestamos
    ALTER COLUMN fecha_actualizacion SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN fecha_actualizacion SET NOT NULL,
    ALTER COLUMN progreso SET DEFAULT 0,
    ALTER COLUMN progreso SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'check_progreso_prestamo'
          AND conrelid = 'prestamos'::regclass
    ) THEN
        ALTER TABLE prestamos
            ADD CONSTRAINT check_progreso_prestamo
            CHECK (progreso BETWEEN 0 AND 100);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_prestamos_usuario_estado
    ON prestamos(usuario_id, estado);

CREATE INDEX IF NOT EXISTS idx_prestamos_libro_estado
    ON prestamos(libro_id, estado);

COMMIT;
