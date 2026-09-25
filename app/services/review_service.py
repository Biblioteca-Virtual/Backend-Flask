from psycopg2 import IntegrityError
from psycopg2 import errors as pg_errors

from app.db import fetch_all, fetch_one, fetch_value
from app.errors.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.review import Resena

_REVIEW_SELECT = """SELECT r.*, l.titulo AS libro_titulo,
                              u.nombre AS usuario_nombre,
                              u.apellido AS usuario_apellido
                   FROM resenas r
                   JOIN libros l ON l.id = r.libro_id
                   JOIN usuarios u ON u.id = r.usuario_id"""


def _get_review_row(review_id):
    return fetch_one(
        f"""{_REVIEW_SELECT}
            WHERE r.id = %s""",
        (review_id,),
    )


def _serialize_review(row):
    return Resena.from_row(row).to_dict()


def list_reviews():
    rows = fetch_all(
        f"""{_REVIEW_SELECT}
            ORDER BY r.id"""
    )
    return [_serialize_review(row) for row in rows]


def get_review(review_id):
    row = _get_review_row(review_id)
    if row is None:
        raise NotFoundError("Reseña")
    return _serialize_review(row)


def create_review(data, usuario_id):
    if fetch_one("SELECT id FROM libros WHERE id = %s", (data["libro_id"],)) is None:
        raise NotFoundError("Libro")
    if fetch_one("SELECT id FROM usuarios WHERE id = %s", (usuario_id,)) is None:
        raise NotFoundError("Usuario")

    try:
        row = fetch_value(
            """INSERT INTO resenas (libro_id, usuario_id, calificacion, comentario)
               VALUES (%s, %s, %s, %s)
               RETURNING id""",
            (data["libro_id"], usuario_id, data["calificacion"], data["comentario"]),
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


def update_review(review_id, data, usuario_id):
    sets = []
    params = []
    for field in ("calificacion", "comentario"):
        if field in data:
            sets.append(f"{field} = %s")
            params.append(data[field])

    if not sets:
        raise ValidationError(
            ["Debe indicar al menos un campo a actualizar entre calificacion, comentario"]
        )

    params.extend((review_id, usuario_id))
    row = fetch_value(
        f"""UPDATE resenas
            SET {', '.join(sets)}
            WHERE id = %s AND usuario_id = %s
            RETURNING id""",
        tuple(params),
    )
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
