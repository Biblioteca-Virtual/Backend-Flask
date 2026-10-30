-- ============================================
-- BIBLIOTECA VIRTUAL - ESQUEMA DE BASE DE DATOS
-- ============================================

-- ============================================
-- TABLA: categorias
-- ============================================

CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT
);


-- ============================================
-- TABLA: autores
-- ============================================

CREATE TABLE IF NOT EXISTS autores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL
);


-- ============================================
-- TABLA: usuarios
-- ============================================

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- TABLA: libros
-- Cada libro pertenece a la biblioteca de un usuario
-- ============================================

CREATE TABLE IF NOT EXISTS libros (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    categoria_id INTEGER NOT NULL DEFAULT 1,
    paginas_totales INTEGER NOT NULL DEFAULT 0,
    paginas_leidas INTEGER NOT NULL DEFAULT 0,
    imagen_portada VARCHAR(500),
    -- Dónde se está leyendo: 'fisico', 'kindle' (Books/Kindle) o 'web'.
    ubicacion VARCHAR(10) NOT NULL DEFAULT 'fisico',
    url_lectura VARCHAR(500),

    CONSTRAINT fk_libro_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_libro_categoria
        FOREIGN KEY (categoria_id)
        REFERENCES categorias(id),

    CONSTRAINT check_ubicacion
        CHECK (ubicacion IN ('fisico', 'kindle', 'web')),

    CONSTRAINT check_paginas_totales
        CHECK (paginas_totales >= 0),

    CONSTRAINT check_paginas_leidas
        CHECK (paginas_leidas >= 0)
);

CREATE INDEX IF NOT EXISTS idx_libros_usuario
    ON libros(usuario_id);

CREATE INDEX IF NOT EXISTS idx_libros_categoria
    ON libros(categoria_id);

CREATE INDEX IF NOT EXISTS idx_libros_titulo
    ON libros(titulo);


-- ============================================
-- TABLA INTERMEDIA: libros_autores
-- Relación N:M entre libros y autores
-- ============================================

CREATE TABLE IF NOT EXISTS libros_autores (
    libro_id INTEGER NOT NULL,
    autor_id INTEGER NOT NULL,

    PRIMARY KEY (libro_id, autor_id),

    CONSTRAINT fk_libro_autor_libro
        FOREIGN KEY (libro_id)
        REFERENCES libros(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_libro_autor_autor
        FOREIGN KEY (autor_id)
        REFERENCES autores(id)
        ON DELETE CASCADE
);


-- ============================================
-- TABLA: resenas
-- ============================================

CREATE TABLE IF NOT EXISTS resenas (
    id SERIAL PRIMARY KEY,
    libro_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    calificacion INTEGER NOT NULL,
    comentario TEXT,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_resena_libro
        FOREIGN KEY (libro_id)
        REFERENCES libros(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_resena_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE,

    CONSTRAINT check_calificacion
        CHECK (calificacion BETWEEN 1 AND 5),

    CONSTRAINT uq_resena_libro_usuario
        UNIQUE (libro_id, usuario_id)
);


-- ============================================
-- TABLA: colecciones
-- Agrupaciones de libros con nombre, propias de cada usuario
-- ============================================

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

CREATE INDEX IF NOT EXISTS idx_colecciones_usuario
    ON colecciones(usuario_id);


-- ============================================
-- TABLA INTERMEDIA: colecciones_libros
-- Relación N:M entre colecciones y libros
-- ============================================

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


-- ============================================
-- DATOS INICIALES: Categorías indispensables para el catálogo
-- ============================================

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

-- Ajustar secuencia de categorías
SELECT setval('categorias_id_seq', COALESCE((SELECT MAX(id) FROM categorias), 1));


-- ============================================
-- DATOS INICIALES: Autores
-- ============================================

INSERT INTO autores (id, nombre, apellido) VALUES
(1, 'Gabriel', 'García Márquez'),
(2, 'Jorge Luis', 'Borges'),
(3, 'Julio', 'Cortázar'),
(4, 'Isabel', 'Allende'),
(5, 'Isaac', 'Asimov')
ON CONFLICT (id) DO NOTHING;

SELECT setval('autores_id_seq', COALESCE((SELECT MAX(id) FROM autores), 1));
