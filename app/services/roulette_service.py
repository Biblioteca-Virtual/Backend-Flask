from app.db import fetch_one
from app.errors.exceptions import ConflictError, NotFoundError
from app.services.reading_service import create_reading

MAX_SPIN_ATTEMPTS = 3


def _select_available_book_id():
    row = fetch_one(
        """SELECT l.id
           FROM libros l
           LEFT JOIN prestamos p ON p.libro_id = l.id AND p.estado = 'activo'
           GROUP BY l.id
           HAVING l.cantidad > COUNT(p.id)
           ORDER BY RANDOM()
           LIMIT 1"""
    )
    return row["id"] if row is not None else None


def spin(usuario_id):
    for _ in range(MAX_SPIN_ATTEMPTS):
        libro_id = _select_available_book_id()
        if libro_id is None:
            break

        try:
            return create_reading(
                {"libro_id": libro_id, "progreso": 0},
                usuario_id,
            )
        except (ConflictError, NotFoundError):
            continue

    raise ConflictError("No hay libros disponibles en este momento")
