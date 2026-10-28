from app.db import fetch_one
from app.errors.exceptions import ConflictError
from app.services.book_service import get_book


def spin(usuario_id=None):
    row = fetch_one("SELECT id FROM libros ORDER BY RANDOM() LIMIT 1")
    if row is None:
        raise ConflictError("No hay libros disponibles en este momento")
    return get_book(row["id"])
