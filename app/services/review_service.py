from psycopg2 import IntegrityError
from psycopg2 import errors as pg_errors

from app.db import fetch_all, fetch_one, fetch_value
from app.errors.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.review import Resena

_QUERY_REVIEW_BY_ID = """SELECT r.*, l.titulo AS libro_titulo,
                                u.nombre AS usuario_nombre,
                                u.apellido AS usuario_apellido
                         FROM resenas r
                         JOIN libros l ON l.id = r.libro_id
                         JOIN usuarios u ON u.id = r.usuario_id
                         WHERE r.id = %s"""

_QUERY_REVIEWS_ALL = """SELECT r.*, l.titulo AS libro_titulo,
                               u.nombre AS usuario_nombre,
                               u.apellido AS usuario_apellido
                        FROM resenas r
                        JOIN libros l ON l.id = r.libro_id
                        JOIN usuarios u ON u.id = r.usuario_id
                        ORDER BY r.id"""

_UPDATE_BOTH = """UPDATE resenas
    SET calificacion = %s, comentario = %s
    WHERE id = %s AND usuario_id = %s
    RETURNING id"""

_UPDATE_RATING = """UPDATE resenas
    SET calificacion = %s
    WHERE id = %s AND usuario_id = %s
    RETURNING id"""

_UPDATE_COMMENT = """UPDATE resenas
    SET comentario = %s
    WHERE id = %s AND usuario_id = %s
    RETURNING id"""


def _get_review_row(review_id):
    return fetch_one(_QUERY_REVIEW_BY_ID, (review_id,))


def get_review(review_id):
    row = _get_review_row(review_id)
    if row is None:
        raise NotFoundError("Reseña")
    return _serialize_review(row)


def _serialize_review(row):
    return Resena.from_row(row).to_dict()


def list_reviews():
    rows = fetch_all(_QUERY_REVIEWS_ALL)
    return [_serialize_review(row) for row in rows]


def _ensure_entities_exist(libro_id, usuario_id):
    if fetch_one("SELECT id FROM libros WHERE id = %s", (libro_id,)) is None:
        raise NotFoundError("Libro")
    if fetch_one("SELECT id FROM usuarios WHERE id = %s", (usuario_id,)) is None:
        raise NotFoundError("Usuario")


def create_review(data, usuario_id):
    _ensure_entities_exist(data["libro_id"], usuario_id)

    try:
        row = fetch_value(
            """INSERT INTO resenas (libro_id, usuario_id, calificacion, comentario)
               VALUES (%s, %s, %s, %s)
               RETURNING id""",
            (data["libro_id"], usuario_id, data["calificacion"], data.get("comentario")),
        )
    except IntegrityError as error:
        if isinstance(error, pg_errors.UniqueViolation) or isinstance(
            getattr(error, "orig", None), pg_errors.UniqueViolation
        ):
            raise ConflictError(
                "Ya existe una reseña de este usuario para este libro"
            ) from error
        raise

    return get_review(row["id"])


def _pick_update_query_and_params(data, review_id, usuario_id):
    has_rating = "calificacion" in data
    has_comment = "comentario" in data

    if has_rating and has_comment:
        return _UPDATE_BOTH, (data["calificacion"], data["comentario"], review_id, usuario_id)
    if has_rating:
        return _UPDATE_RATING, (data["calificacion"], review_id, usuario_id)
    if has_comment:
        return _UPDATE_COMMENT, (data["comentario"], review_id, usuario_id)

    raise ValidationError(
        ["Debe indicar al menos un campo a actualizar entre calificacion, comentario"]
    )


def update_review(review_id, data, usuario_id):
    sql, params = _pick_update_query_and_params(data, review_id, usuario_id)
    row = fetch_value(sql, params)
    if row is None:
        raise NotFoundError("Reseña")

    return get_review(review_id)


def delete_review(review_id, usuario_id):
    row = fetch_value(
        """DELETE FROM resenas
           WHERE id = %s AND usuario_id = %s
           RETURNING id""",
        (review_id, usuario_id),
    )
    if row is None:
        raise NotFoundError("Reseña")
