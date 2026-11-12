-- ======================================================================
-- BIBLIOTECA VIRTUAL - ESQUEMA PARA MYSQL WORKBENCH
-- ----------------------------------------------------------------------
-- Es el mismo esquema de database/init.sql (PostgreSQL) traducido a
-- sintaxis MySQL, para generar el diagrama EER en MySQL Workbench:
--
--   File > Import > Reverse Engineer MySQL Create Script...
--   -> elegir este archivo
--   -> tildar "Place imported objects on a diagram"
--   -> Execute > Next > Finish
--
-- Después: File > Save Model As... para guardarlo como .mwb
--
-- La base real del proyecto sigue siendo PostgreSQL: este archivo es
-- solo para el diagrama.
-- ======================================================================

CREATE SCHEMA IF NOT EXISTS biblioteca_db DEFAULT CHARACTER SET utf8mb4;
USE biblioteca_db;


-- ----------------------------------------------------------------------
-- categorias: catálogo compartido de géneros
-- ----------------------------------------------------------------------
CREATE TABLE categorias (
    id INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE INDEX uq_categorias_nombre (nombre)
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- autores: catálogo compartido de autores
-- ----------------------------------------------------------------------
CREATE TABLE autores (
    id INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    PRIMARY KEY (id)
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- usuarios
-- ----------------------------------------------------------------------
CREATE TABLE usuarios (
    id INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL COMMENT 'Hash Argon2id',
    email_verificado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE INDEX uq_usuarios_email (email)
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- verificaciones_sesion: cada login se confirma por correo
-- ----------------------------------------------------------------------
CREATE TABLE verificaciones_sesion (
    id INT NOT NULL AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    token_hash CHAR(64) NOT NULL COMMENT 'SHA-256 del link del correo',
    consulta_hash CHAR(64) NOT NULL COMMENT 'SHA-256 del secreto de la pestaña de login',
    creada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expira_en TIMESTAMP NOT NULL,
    verificada_en TIMESTAMP NULL,
    entregada BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (id),
    UNIQUE INDEX uq_verificacion_token (token_hash),
    UNIQUE INDEX uq_verificacion_consulta (consulta_hash),
    INDEX idx_verificaciones_sesion_usuario (usuario_id),
    CONSTRAINT fk_verificacion_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- libros: cada libro pertenece a la biblioteca de un usuario
-- ----------------------------------------------------------------------
CREATE TABLE libros (
    id INT NOT NULL AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NULL,
    categoria_id INT NOT NULL DEFAULT 1,
    paginas_totales INT NOT NULL DEFAULT 0,
    paginas_leidas INT NOT NULL DEFAULT 0,
    imagen_portada VARCHAR(500) NULL,
    ubicacion VARCHAR(10) NOT NULL DEFAULT 'fisico' COMMENT 'fisico | kindle | web',
    url_lectura VARCHAR(500) NULL,
    PRIMARY KEY (id),
    INDEX idx_libros_usuario (usuario_id),
    INDEX idx_libros_categoria (categoria_id),
    INDEX idx_libros_titulo (titulo),
    CONSTRAINT fk_libro_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_libro_categoria
        FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        ON DELETE RESTRICT,
    CONSTRAINT check_ubicacion CHECK (ubicacion IN ('fisico', 'kindle', 'web')),
    CONSTRAINT check_paginas_totales CHECK (paginas_totales >= 0),
    CONSTRAINT check_paginas_leidas CHECK (paginas_leidas >= 0)
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- libros_autores: relación N:M entre libros y autores
-- ----------------------------------------------------------------------
CREATE TABLE libros_autores (
    libro_id INT NOT NULL,
    autor_id INT NOT NULL,
    PRIMARY KEY (libro_id, autor_id),
    INDEX idx_libros_autores_autor (autor_id),
    CONSTRAINT fk_libro_autor_libro
        FOREIGN KEY (libro_id) REFERENCES libros (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_libro_autor_autor
        FOREIGN KEY (autor_id) REFERENCES autores (id)
        ON DELETE CASCADE
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- resenas: un usuario reseña cada libro una sola vez
-- ----------------------------------------------------------------------
CREATE TABLE resenas (
    id INT NOT NULL AUTO_INCREMENT,
    libro_id INT NOT NULL,
    usuario_id INT NOT NULL,
    calificacion DECIMAL(2,1) NOT NULL COMMENT '0.5 a 5, de a media estrella',
    comentario TEXT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE INDEX uq_resena_libro_usuario (libro_id, usuario_id),
    INDEX idx_resenas_usuario (usuario_id),
    CONSTRAINT fk_resena_libro
        FOREIGN KEY (libro_id) REFERENCES libros (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_resena_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE,
    CONSTRAINT check_calificacion
        CHECK (calificacion BETWEEN 0.5 AND 5 AND calificacion * 2 = TRUNCATE(calificacion * 2, 0))
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- colecciones: agrupaciones de libros propias de cada usuario
-- ----------------------------------------------------------------------
CREATE TABLE colecciones (
    id INT NOT NULL AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE INDEX uq_coleccion_usuario_nombre (usuario_id, nombre),
    CONSTRAINT fk_coleccion_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE CASCADE
) ENGINE = InnoDB;


-- ----------------------------------------------------------------------
-- colecciones_libros: relación N:M entre colecciones y libros
-- ----------------------------------------------------------------------
CREATE TABLE colecciones_libros (
    coleccion_id INT NOT NULL,
    libro_id INT NOT NULL,
    PRIMARY KEY (coleccion_id, libro_id),
    INDEX idx_colecciones_libros_libro (libro_id),
    CONSTRAINT fk_coleccion_libro_coleccion
        FOREIGN KEY (coleccion_id) REFERENCES colecciones (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_coleccion_libro_libro
        FOREIGN KEY (libro_id) REFERENCES libros (id)
        ON DELETE CASCADE
) ENGINE = InnoDB;
