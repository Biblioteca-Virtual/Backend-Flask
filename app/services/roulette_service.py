from app.db import fetch_one
from app.errors.exceptions import ConflictError
from app.services.book_service import get_book

# Un libro está terminado cuando tiene páginas cargadas y ya se leyeron todas.
_QUERY_RANDOM_PENDING_BOOK = """SELECT id FROM libros
    WHERE usuario_id = %s
      AND NOT (paginas_totales > 0 AND paginas_leidas >= paginas_totales)
    ORDER BY RANDOM()
    LIMIT 1"""


def spin(usuario_id):
    """Elige al azar la próxima lectura entre los libros no terminados del usuario."""
    row = fetch_one(_QUERY_RANDOM_PENDING_BOOK, (usuario_id,))
    if row is None:
        raise ConflictError("No tenés libros pendientes de leer: agregá uno nuevo")
    return get_book(row["id"], usuario_id)
