-- ======================================================================
-- Migración 012: verificación de cada inicio de sesión por correo.
--   Al iniciar sesión se crea una verificación pendiente y se manda el correo
--   con el botón "Verificar Sesión". La sesión (el JWT) recién se entrega
--   cuando se toca ese botón.
--   - token_hash: hash del secreto que va en el link del correo.
--   - consulta_hash: hash del secreto con el que la pestaña del login
--     pregunta si ya se verificó.
--   Se guardan solo los hashes (SHA-256), nunca los secretos.
-- Es idempotente para poder ejecutarla también sobre una base recién inicializada.
-- ======================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS verificaciones_sesion (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    consulta_hash CHAR(64) NOT NULL UNIQUE,
    creada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expira_en TIMESTAMP NOT NULL,
    verificada_en TIMESTAMP,
    entregada BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_verificacion_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_verificaciones_sesion_usuario
    ON verificaciones_sesion (usuario_id);

COMMIT;
