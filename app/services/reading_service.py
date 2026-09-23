from app.db import execute, fetch_all, fetch_one, fetch_value
from app.errors.exceptions import ConflictError, NotFoundError
from app.models.reading import Prestamo


def _get_reading_row(reading_id):
    return fetch_one(
        """SELECT p.*, l.titulo AS libro_titulo,
                  u.nombre AS usuario_nombre, u.apellido AS usuario_apellido
           FROM prestamos p
           JOIN libros l ON l.id = p.libro_id
           JOIN usuarios u ON u.id = p.usuario_id
           WHERE p.id = %s""",
        (reading_id,),
    )


def _serialize_reading(row):
    return Prestamo.from_row(row).to_dict()


def list_readings():
    rows = fetch_all(
        """SELECT p.*, l.titulo AS libro_titulo,
                  u.nombre AS usuario_nombre, u.apellido AS usuario_apellido
           FROM prestamos p
           JOIN libros l ON l.id = p.libro_id
           JOIN usuarios u ON u.id = p.usuario_id
           ORDER BY p.id"""
    )
    return [_serialize_reading(row) for row in rows]


def get_reading(reading_id):
    row = _get_reading_row(reading_id)
    if row is None:
        raise NotFoundError("Lectura")
    return _serialize_reading(row)


def create_reading(data):
    if fetch_one("SELECT id FROM usuarios WHERE id = %s", (data["usuario_id"],)) is None:
        raise NotFoundError("Usuario")

    libro = fetch_one(
        "SELECT id, cantidad FROM libros WHERE id = %s",
        (data["libro_id"],),
    )
    if libro is None:
        raise NotFoundError("Libro")

    active = fetch_one(
        """SELECT COUNT(*) AS total
           FROM prestamos
           WHERE libro_id = %s AND estado = 'activo'""",
        (data["libro_id"],),
    )["total"]
    if active >= libro["cantidad"]:
        raise ConflictError("No hay copias disponibles de este libro")

    row = fetch_value(
        "INSERT INTO prestamos (usuario_id, libro_id) VALUES (%s, %s) RETURNING id",
        (data["usuario_id"], data["libro_id"]),
    )
    return get_reading(row["id"])


def update_reading(reading_id, data):
    if _get_reading_row(reading_id) is None:
        raise NotFoundError("Lectura")

    if data["estado"] == "devuelto":
        execute(
            """UPDATE prestamos
               SET estado = 'devuelto', fecha_devolucion = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (reading_id,),
        )
    else:
        execute(
            """UPDATE prestamos
               SET estado = 'activo', fecha_devolucion = NULL
               WHERE id = %s""",
            (reading_id,),
        )
    return get_reading(reading_id)


def delete_reading(reading_id):
    if _get_reading_row(reading_id) is None:
        raise NotFoundError("Lectura")
    execute("DELETE FROM prestamos WHERE id = %s", (reading_id,))