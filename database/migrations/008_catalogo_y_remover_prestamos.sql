-- ======================================================================
-- Migración 008: soporte de páginas totales, páginas leídas y portada en libros,
-- remoción de prestamos y carga de categorías iniciales.
-- ======================================================================
BEGIN;

-- 1. Agregar columnas a libros si no existen
ALTER TABLE libros
    ADD COLUMN IF NOT EXISTS paginas_totales INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS paginas_leidas INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS imagen_portada VARCHAR(500);

-- Asegurar valor por defecto para categoria_id
ALTER TABLE libros
    ALTER COLUMN categoria_id SET DEFAULT 1;

-- 2. Asegurar categorías iniciales
INSERT INTO categorias (id, nombre, descripcion) VALUES
(1, 'General', 'Libros generales, misceláneos y divulgación general'),
(2, 'Novela', 'Novelas literarias y narrativa clásica o contemporánea'),
(3, 'Ciencia Ficción', 'Relatos futuristas, distopías y universos paralelos'),
(4, 'Fantasía', 'Literatura de fantasía épica, magia y mundos imaginarios'),
(5, 'Historia', 'Acontecimientos históricos, biografías y crónicas'),
(6, 'Tecnología', 'Desarrollo de software, ciencias de la computación y tecnología'),
(7, 'Misterio y Suspenso', 'Novela policíaca, intriga y crímenes')
ON CONFLICT (id) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion;

SELECT setval('categorias_id_seq', COALESCE((SELECT MAX(id) FROM categorias), 1));

-- 3. Eliminar tabla prestamos de la base de datos si existe
DROP TABLE IF EXISTS prestamos CASCADE;

COMMIT;
