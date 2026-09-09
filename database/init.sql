-- ============================================
-- BIBLIOTECA VIRTUAL
-- Issue #3 - Modelo y esquema de datos
-- ============================================

-- ============================================
-- TABLA: categorias
-- ============================================

CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT
);


-- ============================================
-- TABLA: autores
-- ============================================

CREATE TABLE autores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL
);


-- ============================================
-- TABLA: usuarios
-- ============================================

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- TABLA: libros
-- ============================================

CREATE TABLE libros (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    descripcion TEXT,
    anio_publicacion INTEGER,
    cantidad INTEGER NOT NULL DEFAULT 1,
    categoria_id INTEGER NOT NULL,

    CONSTRAINT fk_libro_categoria
        FOREIGN KEY (categoria_id)
        REFERENCES categorias(id),

    CONSTRAINT check_anio_publicacion
        CHECK (
            anio_publicacion IS NULL
            OR anio_publicacion > 0
        ),

    CONSTRAINT check_cantidad
        CHECK (cantidad >= 0)
);


-- ============================================
-- TABLA INTERMEDIA: libros_autores
-- Relación N:M entre libros y autores
-- ============================================

CREATE TABLE libros_autores (
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
-- TABLA: prestamos
-- ============================================

CREATE TABLE prestamos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    libro_id INTEGER NOT NULL,
    fecha_prestamo TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_devolucion TIMESTAMP,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',

    CONSTRAINT fk_prestamo_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id),

    CONSTRAINT fk_prestamo_libro
        FOREIGN KEY (libro_id)
        REFERENCES libros(id),

    CONSTRAINT check_estado_prestamo
        CHECK (estado IN ('activo', 'devuelto')),

    CONSTRAINT check_fecha_devolucion
        CHECK (
            fecha_devolucion IS NULL
            OR fecha_devolucion >= fecha_prestamo
        )
);