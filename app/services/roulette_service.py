from app.db import fetch_one
from app.errors.exceptions import ConflictError
from app.services.book_service import get_book


def spin():
    row = fetch_one(
        """SELECT l.id
           FROM libros l
           LEFT JOIN prestamos p ON p.libro_id = l.id AND p.estado = 'activo'
           GROUP BY l.id
           HAVING l.cantidad > COUNT(p.id)
           ORDER BY RANDOM()
           LIMIT 1"""
    )
    if row is None:
        raise ConflictError("No hay libros disponibles en este momento")
    return get_book(row["id"])