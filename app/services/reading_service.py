from app.db import fetch_all, fetch_one, fetch_value, transaction
from app.errors.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.reading import Prestamo

_QUERY_READING_BY_ID = """SELECT p.*, l.titulo AS libro_titulo,
                                  u.nombre AS usuario_nombre,
                                  u.apellido AS usuario_apellido
                           FROM prestamos p
                           JOIN libros l ON l.id = p.libro_id
                           JOIN usuarios u ON u.id = p.usuario_id
                           WHERE p.id = %s AND p.usuario_id = %s"""

_QUERY_READINGS_LIST = """SELECT p.*, l.titulo AS libro_titulo,
                                 u.nombre AS usuario_nombre,
                                 u.apellido AS usuario_apellido
                          FROM prestamos p
                          JOIN libros l ON l.id = p.libro_id
                          JOIN usuarios u ON u.id = p.usuario_id
                          WHERE p.usuario_id = %s
                            AND (%s IS NULL OR p.estado = %s)
                            AND (%s IS NULL OR p.libro_id = %s)
                          ORDER BY p.fecha_actualizacion DESC, p.id DESC"""


def _get_reading_row(reading_id, usuario_id):
    return fetch_one(_QUERY_READING_BY_ID, (reading_id, usuario_id))


def _get_reading_row_for_update(cursor, reading_id, usuario_id):
    cursor.execute(
        """SELECT p.*, l.titulo AS libro_titulo,
                  l.cantidad AS libro_cantidad,
                  u.nombre AS usuario_nombre,
                  u.apellido AS usuario_apellido
           FROM prestamos p
           JOIN libros l ON l.id = p.libro_id
           JOIN usuarios u ON u.id = p.usuario_id
           WHERE p.id = %s AND p.usuario_id = %s
           FOR UPDATE OF p, l""",
        (reading_id, usuario_id),
    )
    return cursor.fetchone()


def _active_count(cursor, book_id, excluded_reading_id=None):
    if excluded_reading_id is None:
        cursor.execute(
            """SELECT COUNT(*) AS total
               FROM prestamos
               WHERE libro_id = %s AND estado = 'activo'""",
            (book_id,),
        )
    else:
        cursor.execute(
            """SELECT COUNT(*) AS total
               FROM prestamos
               WHERE libro_id = %s
                 AND estado = 'activo'
                 AND id <> %s""",
            (book_id, excluded_reading_id),
        )
    return cursor.fetchone()["total"]


def _serialize_reading(row):
    return Prestamo.from_row(row).to_dict()


def list_readings(usuario_id, estado=None, libro_id=None):
    rows = fetch_all(
        _QUERY_READINGS_LIST,
        (usuario_id, estado, estado, libro_id, libro_id),
    )
    return [_serialize_reading(row) for row in rows]


def get_reading(reading_id, usuario_id):
    row = _get_reading_row(reading_id, usuario_id)
    if row is None:
        raise NotFoundError("Lectura")
    return _serialize_reading(row)


def _check_valid_progress(progress):
    if (
        isinstance(progress, bool)
        or not isinstance(progress, int)
        or not 0 <= progress <= 100
    ):
        raise ValidationError(["progreso debe ser un entero entre 0 y 100"])


def _check_valid_state(estado):
    if not isinstance(estado, str) or estado not in {"activo", "devuelto"}:
        raise ValidationError(
            ["estado debe ser uno de los siguientes valores: activo, devuelto"]
        )


def _lock_book_and_ensure_copies(cursor, book_id):
    cursor.execute(
        """SELECT id, cantidad
           FROM libros
           WHERE id = %s
           FOR UPDATE""",
        (book_id,),
    )
    book = cursor.fetchone()
    if book is None:
        raise NotFoundError("Libro")

    active = _active_count(cursor, book_id)
    if active >= book["cantidad"]:
        raise ConflictError("No hay copias disponibles de este libro")


def create_reading(data, usuario_id):
    with transaction() as cursor:
        _lock_book_and_ensure_copies(cursor, data["libro_id"])

        progress = data.get("progreso", 0)
        _check_valid_progress(progress)

        cursor.execute(
            """INSERT INTO prestamos (usuario_id, libro_id, progreso)
               VALUES (%s, %s, %s)
               RETURNING id""",
            (usuario_id, data["libro_id"], progress),
        )
        reading_id = cursor.fetchone()["id"]

    return get_reading(reading_id, usuario_id)


def _check_reactivation_available(cursor, current, target_state, reading_id):
    if current["estado"] == "devuelto" and target_state == "activo":
        active = _active_count(
            cursor,
            current["libro_id"],
            excluded_reading_id=reading_id,
        )
        if active >= current["libro_cantidad"]:
            raise ConflictError("No hay copias disponibles de este libro")


_UPDATE_ACTIVE_READING = """UPDATE prestamos
    SET progreso = %s,
        estado = %s,
        fecha_devolucion = NULL,
        fecha_actualizacion = CURRENT_TIMESTAMP
    WHERE id = %s AND usuario_id = %s"""

_UPDATE_RETURNED_READING = """UPDATE prestamos
    SET progreso = %s,
        estado = %s,
        fecha_devolucion = COALESCE(fecha_devolucion, CURRENT_TIMESTAMP),
        fecha_actualizacion = CURRENT_TIMESTAMP
    WHERE id = %s AND usuario_id = %s"""


def update_reading(reading_id, data, usuario_id):
    with transaction() as cursor:
        current = _get_reading_row_for_update(cursor, reading_id, usuario_id)
        if current is None:
            raise NotFoundError("Lectura")

        progress = data.get("progreso", current["progreso"])
        _check_valid_progress(progress)

        estado = data.get("estado", current["estado"])
        _check_valid_state(estado)

        _check_reactivation_available(cursor, current, estado, reading_id)

        sql = _UPDATE_ACTIVE_READING if estado == "activo" else _UPDATE_RETURNED_READING
        cursor.execute(sql, (progress, estado, reading_id, usuario_id))

    return get_reading(reading_id, usuario_id)


def delete_reading(reading_id, usuario_id):
    deleted = fetch_value(
        """DELETE FROM prestamos
           WHERE id = %s AND usuario_id = %s
           RETURNING id""",
        (reading_id, usuario_id),
    )
    if deleted is None:
        raise NotFoundError("Lectura")
