-- ======================================================================
-- Migración 013: las reseñas admiten medias estrellas.
--   calificacion pasa de INTEGER (1 a 5) a NUMERIC(2,1) (0.5 a 5, de a 0.5).
--   Las reseñas existentes conservan su valor.
-- Es idempotente para poder ejecutarla también sobre una base recién inicializada.
-- ======================================================================
BEGIN;

ALTER TABLE resenas DROP CONSTRAINT IF EXISTS check_calificacion;

ALTER TABLE resenas ALTER COLUMN calificacion TYPE NUMERIC(2,1);

ALTER TABLE resenas ADD CONSTRAINT check_calificacion
    CHECK (calificacion BETWEEN 0.5 AND 5 AND calificacion * 2 = TRUNC(calificacion * 2));

COMMIT;
