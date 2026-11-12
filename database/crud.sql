-- ======================================================================
-- BIBLIOTECA VIRTUAL - GESTIÓN DE DATOS (CRUD)
-- ----------------------------------------------------------------------
-- Ejemplos de Create / Read / Update / Delete sobre todas las tablas,
-- respetando las relaciones definidas en init.sql.
--
-- Cómo ejecutarlo (con la base levantada en Docker):
--   docker exec -i biblioteca_postgres psql -U biblioteca_user -d biblioteca_db < database/crud.sql
--
-- Todo corre dentro de una transacción que termina en ROLLBACK, así que
-- NO deja datos en la base: sirve para probar y mostrar el CRUD sin
-- ensuciar nada. Si querés que los cambios queden guardados, cambiá el
-- ROLLBACK del final por COMMIT.
--
-- Para no depender de ids fijos, los registros se buscan por un dato
-- único (email del usuario, título del libro, nombre de la colección).
-- ======================================================================

BEGIN;


-- ======================================================================
-- 1. USUARIOS
-- ======================================================================

-- CREATE: registrar un usuario.
-- En la app la contraseña llega hasheada con Argon2id desde Flask; acá va
-- un hash de ejemplo porque la base nunca guarda la contraseña en texto plano.
INSERT INTO usuarios (nombre, apellido, email, password)
VALUES ('Lucía', 'Pérez', 'lucia.demo@example.com',
        '$argon2id$v=19$m=65536,t=3,p=4$ZGVtb3NhbHQ$ZGVtb2hhc2hkZW1vaGFzaA')
RETURNING id, nombre, apellido, email, email_verificado, fecha_registro;

-- READ: buscar un usuario por email (como hace el login), sin traer la contraseña.
SELECT id, nombre, apellido, email, email_verificado, fecha_registro
FROM usuarios
WHERE email = 'lucia.demo@example.com';

-- UPDATE: marcar el email como verificado (lo que pasa al tocar el link del correo).
UPDATE usuarios
SET email_verificado = TRUE
WHERE email = 'lucia.demo@example.com'
RETURNING id, email, email_verificado;


-- ======================================================================
-- 2. VERIFICACIONES DE SESIÓN  (usuarios 1 ── N verificaciones_sesion)
-- ======================================================================

-- CREATE: al iniciar sesión se crea una verificación pendiente que vence en 15 min.
-- Se guardan solo hashes SHA-256 (64 caracteres hex) de los secretos.
INSERT INTO verificaciones_sesion (usuario_id, token_hash, consulta_hash, expira_en)
SELECT id,
       md5('token-demo')    || md5('token-demo-2'),
       md5('consulta-demo') || md5('consulta-demo-2'),
       CURRENT_TIMESTAMP + INTERVAL '15 minutes'
FROM usuarios
WHERE email = 'lucia.demo@example.com'
RETURNING id, usuario_id, expira_en, verificada_en, entregada;

-- READ: verificaciones pendientes y vigentes de un usuario.
SELECT v.id, v.creada_en, v.expira_en
FROM verificaciones_sesion v
JOIN usuarios u ON u.id = v.usuario_id
WHERE u.email = 'lucia.demo@example.com'
  AND v.verificada_en IS NULL
  AND v.expira_en > CURRENT_TIMESTAMP;

-- UPDATE: el usuario tocó "Verificar Sesión" en el correo.
UPDATE verificaciones_sesion
SET verificada_en = CURRENT_TIMESTAMP
WHERE token_hash = md5('token-demo') || md5('token-demo-2')
  AND verificada_en IS NULL
  AND expira_en > CURRENT_TIMESTAMP
RETURNING id, verificada_en;

-- UPDATE: la pestaña del login ya recibió el JWT.
UPDATE verificaciones_sesion
SET entregada = TRUE
WHERE consulta_hash = md5('consulta-demo') || md5('consulta-demo-2')
RETURNING id, entregada;

-- DELETE: limpieza de verificaciones vencidas que nunca se confirmaron.
DELETE FROM verificaciones_sesion
WHERE expira_en < CURRENT_TIMESTAMP
  AND verificada_en IS NULL;


-- ======================================================================
-- 3. CATEGORÍAS  (catálogo compartido)
-- ======================================================================

-- CREATE: nueva categoría (si ya existe con ese nombre, no la duplica).
INSERT INTO categorias (nombre, descripcion)
VALUES ('Poesía', 'Poemarios y antologías')
ON CONFLICT (nombre) DO NOTHING
RETURNING id, nombre;

-- READ: todas las categorías con cuántos libros tiene cada una.
SELECT c.id, c.nombre, COUNT(l.id) AS cantidad_libros
FROM categorias c
LEFT JOIN libros l ON l.categoria_id = c.id
GROUP BY c.id
ORDER BY c.nombre;

-- UPDATE: cambiar la descripción.
UPDATE categorias
SET descripcion = 'Poemarios, antologías y poesía contemporánea'
WHERE nombre = 'Poesía'
RETURNING id, nombre, descripcion;


-- ======================================================================
-- 4. AUTORES  (catálogo compartido)
-- ======================================================================

-- CREATE
INSERT INTO autores (nombre, apellido)
VALUES ('Alejandra', 'Pizarnik')
RETURNING id, nombre, apellido;

-- READ: autores ordenados por apellido.
SELECT id, nombre, apellido
FROM autores
ORDER BY apellido, nombre;

-- UPDATE
UPDATE autores
SET nombre = 'Flora Alejandra'
WHERE nombre = 'Alejandra' AND apellido = 'Pizarnik'
RETURNING id, nombre, apellido;


-- ======================================================================
-- 5. LIBROS  (usuarios 1 ── N libros, categorias 1 ── N libros)
-- ======================================================================

-- CREATE: agregar un libro a la biblioteca de un usuario.
INSERT INTO libros (usuario_id, titulo, descripcion, categoria_id,
                    paginas_totales, paginas_leidas, ubicacion)
SELECT u.id, 'Árbol de Diana', 'Poemario de 1962', c.id, 64, 0, 'fisico'
FROM usuarios u, categorias c
WHERE u.email = 'lucia.demo@example.com'
  AND c.nombre = 'Poesía'
RETURNING id, titulo, categoria_id, ubicacion;

-- CREATE: un segundo libro que se lee en la web (url_lectura).
INSERT INTO libros (usuario_id, titulo, categoria_id, paginas_totales, ubicacion, url_lectura)
SELECT id, 'Ficciones', 2, 200, 'web', 'https://example.com/ficciones'
FROM usuarios
WHERE email = 'lucia.demo@example.com'
RETURNING id, titulo, ubicacion, url_lectura;

-- READ: la biblioteca de un usuario con categoría y porcentaje de progreso.
SELECT l.id,
       l.titulo,
       c.nombre AS categoria,
       l.paginas_leidas || '/' || l.paginas_totales AS paginas,
       CASE WHEN l.paginas_totales > 0
            THEN ROUND(l.paginas_leidas * 100.0 / l.paginas_totales)
            ELSE 0
       END AS progreso_pct,
       l.ubicacion
FROM libros l
JOIN usuarios u   ON u.id = l.usuario_id
JOIN categorias c ON c.id = l.categoria_id
WHERE u.email = 'lucia.demo@example.com'
ORDER BY l.titulo;

-- UPDATE: registrar avance de lectura.
UPDATE libros
SET paginas_leidas = 32
WHERE titulo = 'Árbol de Diana'
  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
RETURNING id, titulo, paginas_leidas, paginas_totales;

-- UPDATE: cambiar dónde se está leyendo (pasa a Kindle).
UPDATE libros
SET ubicacion = 'kindle', url_lectura = NULL
WHERE titulo = 'Ficciones'
  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
RETURNING id, titulo, ubicacion;


-- ======================================================================
-- 6. LIBROS_AUTORES  (libros N ── M autores)
-- ======================================================================

-- CREATE: asignar autores a los libros.
INSERT INTO libros_autores (libro_id, autor_id)
SELECT l.id, a.id
FROM libros l, autores a
WHERE l.titulo = 'Árbol de Diana' AND a.apellido = 'Pizarnik'
ON CONFLICT DO NOTHING;

INSERT INTO libros_autores (libro_id, autor_id)
SELECT l.id, a.id
FROM libros l, autores a
WHERE l.titulo = 'Ficciones' AND a.apellido = 'Borges'
ON CONFLICT DO NOTHING;

-- READ: cada libro con todos sus autores en una sola columna.
SELECT l.titulo,
       STRING_AGG(a.nombre || ' ' || a.apellido, ', ' ORDER BY a.apellido) AS autores
FROM libros l
JOIN libros_autores la ON la.libro_id = l.id
JOIN autores a         ON a.id = la.autor_id
WHERE l.usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
GROUP BY l.id
ORDER BY l.titulo;

-- (En una tabla intermedia no hay UPDATE: para "cambiar" un autor se borra
--  la fila y se inserta la nueva, que es lo que hace el backend.)

-- DELETE: quitar un autor de un libro.
DELETE FROM libros_autores
WHERE libro_id = (SELECT id FROM libros WHERE titulo = 'Ficciones'
                  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com'))
  AND autor_id = (SELECT id FROM autores WHERE apellido = 'Borges');


-- ======================================================================
-- 7. RESEÑAS  (libros 1 ── N resenas, usuarios 1 ── N resenas)
--    Un usuario reseña cada libro una sola vez (UNIQUE libro_id, usuario_id).
-- ======================================================================

-- CREATE: calificación con media estrella (0.5 a 5, de a 0.5).
INSERT INTO resenas (libro_id, usuario_id, calificacion, comentario)
SELECT l.id, l.usuario_id, 4.5, 'Muy intenso, para leer despacio.'
FROM libros l
WHERE l.titulo = 'Árbol de Diana'
  AND l.usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
RETURNING id, libro_id, calificacion, comentario;

-- READ: reseñas con el título del libro y el nombre de quien la escribió.
SELECT r.id,
       l.titulo,
       u.nombre || ' ' || u.apellido AS autor_resena,
       r.calificacion,
       r.comentario,
       r.fecha_creacion
FROM resenas r
JOIN libros l   ON l.id = r.libro_id
JOIN usuarios u ON u.id = r.usuario_id
WHERE u.email = 'lucia.demo@example.com'
ORDER BY r.fecha_creacion DESC;

-- READ: promedio de calificación por libro.
SELECT l.titulo, ROUND(AVG(r.calificacion), 1) AS promedio, COUNT(*) AS cantidad
FROM resenas r
JOIN libros l ON l.id = r.libro_id
GROUP BY l.id
ORDER BY promedio DESC;

-- UPDATE: editar calificación y comentario.
UPDATE resenas
SET calificacion = 5, comentario = 'Releído: es una obra maestra.'
WHERE libro_id = (SELECT id FROM libros WHERE titulo = 'Árbol de Diana'
                  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com'))
  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
RETURNING id, calificacion, comentario;


-- ======================================================================
-- 8. COLECCIONES  (usuarios 1 ── N colecciones)
--    El nombre no se repite para el mismo usuario (UNIQUE usuario_id, nombre).
-- ======================================================================

-- CREATE
INSERT INTO colecciones (usuario_id, nombre)
SELECT id, 'Para el verano'
FROM usuarios
WHERE email = 'lucia.demo@example.com'
RETURNING id, nombre, fecha_creacion;

-- UPDATE: renombrar.
UPDATE colecciones
SET nombre = 'Lecturas de verano'
WHERE nombre = 'Para el verano'
  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
RETURNING id, nombre;


-- ======================================================================
-- 9. COLECCIONES_LIBROS  (colecciones N ── M libros)
-- ======================================================================

-- CREATE: meter los dos libros del usuario en su colección.
INSERT INTO colecciones_libros (coleccion_id, libro_id)
SELECT c.id, l.id
FROM colecciones c
JOIN libros l ON l.usuario_id = c.usuario_id
WHERE c.nombre = 'Lecturas de verano'
  AND c.usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
ON CONFLICT DO NOTHING;

-- READ: colecciones del usuario con cuántos libros tiene cada una
-- (LEFT JOIN para que una colección vacía aparezca con 0).
SELECT c.id, c.nombre, COUNT(cl.libro_id) AS cantidad_libros
FROM colecciones c
LEFT JOIN colecciones_libros cl ON cl.coleccion_id = c.id
WHERE c.usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
GROUP BY c.id
ORDER BY c.id;

-- READ: libros que hay dentro de una colección.
SELECT c.nombre AS coleccion, l.titulo
FROM colecciones c
JOIN colecciones_libros cl ON cl.coleccion_id = c.id
JOIN libros l              ON l.id = cl.libro_id
WHERE c.nombre = 'Lecturas de verano'
ORDER BY l.titulo;

-- DELETE: sacar un libro de la colección (el libro sigue en la biblioteca).
DELETE FROM colecciones_libros
WHERE coleccion_id = (SELECT id FROM colecciones WHERE nombre = 'Lecturas de verano')
  AND libro_id = (SELECT id FROM libros WHERE titulo = 'Ficciones'
                  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com'));


-- ======================================================================
-- 10. PRUEBAS DE INTEGRIDAD
--     Muestran que la base rechaza datos inválidos por sí sola.
--     Cada intento va en un bloque que atrapa el error y lo informa
--     con un NOTICE, así el script sigue corriendo.
-- ======================================================================

DO $$
BEGIN
    -- FK: no se puede crear un libro para un usuario que no existe.
    BEGIN
        INSERT INTO libros (usuario_id, titulo) VALUES (-1, 'Libro huérfano');
        RAISE NOTICE 'FALLO: se aceptó un libro sin usuario';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'OK  FK: libro con usuario inexistente rechazado';
    END;

    -- CHECK: ubicación fuera de {fisico, kindle, web}.
    BEGIN
        INSERT INTO libros (usuario_id, titulo, ubicacion)
        SELECT id, 'Libro raro', 'tablet' FROM usuarios WHERE email = 'lucia.demo@example.com';
        RAISE NOTICE 'FALLO: se aceptó ubicacion = tablet';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK  CHECK: ubicacion inválida rechazada';
    END;

    -- CHECK: calificación que no es múltiplo de 0.5.
    BEGIN
        UPDATE resenas SET calificacion = 3.7
        WHERE usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com');
        RAISE NOTICE 'FALLO: se aceptó calificacion = 3.7';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'OK  CHECK: calificación 3.7 rechazada';
    END;

    -- UNIQUE: el mismo usuario no puede reseñar dos veces el mismo libro.
    BEGIN
        INSERT INTO resenas (libro_id, usuario_id, calificacion)
        SELECT libro_id, usuario_id, 3 FROM resenas
        WHERE usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
        LIMIT 1;
        RAISE NOTICE 'FALLO: se aceptó una reseña duplicada';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'OK  UNIQUE: reseña duplicada rechazada';
    END;

    -- UNIQUE: email repetido.
    BEGIN
        INSERT INTO usuarios (nombre, apellido, email, password)
        VALUES ('Otra', 'Persona', 'lucia.demo@example.com', 'x');
        RAISE NOTICE 'FALLO: se aceptó un email repetido';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'OK  UNIQUE: email repetido rechazado';
    END;

    -- FK sin CASCADE: no se puede borrar una categoría que tiene libros.
    BEGIN
        DELETE FROM categorias WHERE nombre = 'Poesía';
        RAISE NOTICE 'FALLO: se borró una categoría en uso';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'OK  FK: categoría con libros no se puede borrar';
    END;
END;
$$;


-- ======================================================================
-- 11. DELETE EN CASCADA
--     Las FK con ON DELETE CASCADE borran solas las filas dependientes.
-- ======================================================================

-- Antes de borrar: cuántas filas dependen del libro "Árbol de Diana".
SELECT
    (SELECT COUNT(*) FROM resenas r            JOIN libros l ON l.id = r.libro_id  WHERE l.titulo = 'Árbol de Diana') AS resenas,
    (SELECT COUNT(*) FROM libros_autores la    JOIN libros l ON l.id = la.libro_id WHERE l.titulo = 'Árbol de Diana') AS autores,
    (SELECT COUNT(*) FROM colecciones_libros cl JOIN libros l ON l.id = cl.libro_id WHERE l.titulo = 'Árbol de Diana') AS colecciones;

-- DELETE: borrar el libro. Se van con él sus reseñas, sus filas en
-- libros_autores y en colecciones_libros (el autor y la colección quedan).
DELETE FROM libros
WHERE titulo = 'Árbol de Diana'
  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
RETURNING id, titulo;

-- DELETE: borrar la colección (sus libros siguen en la biblioteca).
DELETE FROM colecciones
WHERE nombre = 'Lecturas de verano'
  AND usuario_id = (SELECT id FROM usuarios WHERE email = 'lucia.demo@example.com')
RETURNING id, nombre;

-- DELETE: borrar el usuario. Arrastra en cascada sus libros, reseñas,
-- colecciones y verificaciones de sesión.
DELETE FROM usuarios
WHERE email = 'lucia.demo@example.com'
RETURNING id, email;

-- Comprobación: no quedó nada del usuario de prueba.
SELECT
    (SELECT COUNT(*) FROM libros      WHERE titulo IN ('Árbol de Diana', 'Ficciones')) AS libros_restantes,
    (SELECT COUNT(*) FROM colecciones WHERE nombre = 'Lecturas de verano')            AS colecciones_restantes;

-- DELETE en catálogos: ahora que la categoría y el autor no se usan, se pueden borrar.
DELETE FROM categorias WHERE nombre = 'Poesía'     RETURNING id, nombre;
DELETE FROM autores    WHERE apellido = 'Pizarnik' RETURNING id, nombre, apellido;


-- Deshace todo lo anterior. Cambiar por COMMIT para guardar los cambios.
ROLLBACK;
