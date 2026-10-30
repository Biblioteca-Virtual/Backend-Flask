from psycopg2 import IntegrityError
from psycopg2 import errors as pg_errors

from app.db import fetch_all, fetch_one, fetch_value
from app.errors.exceptions import ConflictError, NotFoundError
from app.models.collection import Coleccion
from app.services.book_service import get_book

_QUERY_COLLECTIONS_BY_USER = """SELECT c.*, COUNT(cl.libro_id) AS cantidad_libros
    FROM colecciones c
    LEFT JOIN colecciones_libros cl ON cl.coleccion_id = c.id
    WHERE c.usuario_id = %s
    GROUP BY c.id
    ORDER BY c.id"""

_QUERY_COLLECTION_BY_ID = """SELECT c.*, COUNT(cl.libro_id) AS cantidad_libros
    FROM colecciones c
    LEFT JOIN colecciones_libros cl ON cl.coleccion_id = c.id
    WHERE c.id = %s AND c.usuario_id = %s
    GROUP BY c.id"""

_QUERY_LIBRO_IDS = """SELECT libro_id
    FROM colecciones_libros
    WHERE coleccion_id = %s
    ORDER BY libro_id"""


def _is_unique_violation(error):
    return isinstance(error, pg_errors.UniqueViolation) or isinstance(
        getattr(error, "orig", None), pg_errors.UniqueViolation
    )


def _get_collection_row(collection_id, usuario_id):
    row = fetch_one(_QUERY_COLLECTION_BY_ID, (collection_id, usuario_id))
    if row is None:
        raise NotFoundError("Colección")
    return row


def list_collections(usuario_id):
    rows = fetch_all(_QUERY_COLLECTIONS_BY_USER, (usuario_id,))
    return [Coleccion.from_row(row).to_dict() for row in rows]


def get_collection(collection_id, usuario_id):
    coleccion = Coleccion.from_row(_get_collection_row(collection_id, usuario_id))
    rows = fetch_all(_QUERY_LIBRO_IDS, (collection_id,))
    coleccion.libros = [get_book(row["libro_id"], usuario_id) for row in rows]
    return coleccion.to_dict()


def create_collection(data, usuario_id):
    try:
        row = fetch_value(
            """INSERT INTO colecciones (usuario_id, nombre)
               VALUES (%s, %s)
               RETURNING id""",
            (usuario_id, data["nombre"]),
        )
    except IntegrityError as error:
        if _is_unique_violation(error):
            raise ConflictError("Ya tenés una colección con ese nombre") from error
        raise
    return get_collection(row["id"], usuario_id)


def rename_collection(collection_id, data, usuario_id):
    try:
        row = fetch_value(
            """UPDATE colecciones SET nombre = %s
               WHERE id = %s AND usuario_id = %s
               RETURNING id""",
            (data["nombre"], collection_id, usuario_id),
        )
    except IntegrityError as error:
        if _is_unique_violation(error):
            raise ConflictError("Ya tenés una colección con ese nombre") from error
        raise
    if row is None:
        raise NotFoundError("Colección")
    return get_collection(collection_id, usuario_id)


def delete_collection(collection_id, usuario_id):
    row = fetch_value(
        """DELETE FROM colecciones
           WHERE id = %s AND usuario_id = %s
           RETURNING id""",
        (collection_id, usuario_id),
    )
    if row is None:
        raise NotFoundError("Colección")


def add_book_to_collection(collection_id, libro_id, usuario_id):
    _get_collection_row(collection_id, usuario_id)
    if fetch_one(
        "SELECT id FROM libros WHERE id = %s AND usuario_id = %s", (libro_id, usuario_id)
    ) is None:
        raise NotFoundError("Libro")
    fetch_value(
        """INSERT INTO colecciones_libros (coleccion_id, libro_id)
           VALUES (%s, %s)
           ON CONFLICT DO NOTHING
           RETURNING coleccion_id""",
        (collection_id, libro_id),
    )
    return get_collection(collection_id, usuario_id)


def remove_book_from_collection(collection_id, libro_id, usuario_id):
    _get_collection_row(collection_id, usuario_id)
    row = fetch_value(
        """DELETE FROM colecciones_libros
           WHERE coleccion_id = %s AND libro_id = %s
           RETURNING libro_id""",
        (collection_id, libro_id),
    )
    if row is None:
        raise NotFoundError("Libro en la colección")
    return get_collection(collection_id, usuario_id)
