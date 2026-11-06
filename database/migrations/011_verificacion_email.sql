-- ======================================================================
-- Migración 011: verificación del email al registrarse.
--   - usuarios.email_verificado: las cuentas nuevas empiezan sin verificar y
--     no pueden iniciar sesión hasta tocar el link del correo.
--   - Las cuentas que ya existían quedan verificadas para no dejarlas afuera.
-- Es idempotente para poder ejecutarla también sobre una base recién inicializada.
-- ======================================================================
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'usuarios' AND column_name = 'email_verificado'
    ) THEN
        ALTER TABLE usuarios ADD COLUMN email_verificado BOOLEAN NOT NULL DEFAULT FALSE;
        UPDATE usuarios SET email_verificado = TRUE;
    END IF;
END $$;

COMMIT;
