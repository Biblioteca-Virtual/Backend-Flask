from app.db import execute, fetch_all, fetch_one, fetch_value
from app.errors.exceptions import NotFoundError
from app.models.review import Resena


def _get_review_row(review_id):
    return fetch_one(
        """SELECT r.*, l.titulo AS libro_titulo,
                  u.nombre AS usuario_nombre, u.apellido AS usuario_apellido
           FROM resenas r
           JOIN libros l ON l.id = r.libro_id
           JOIN usuarios u ON u.id = r.usuario_id
           WHERE r.id = %s""",
        (review_id,),
    )


def _serialize_review(row):
    return Resena.from_row(row).to_dict()


def list_reviews():
    rows = fetch_all(
        """SELECT r.*, l.titulo AS libro_titulo,
                  u.nombre AS usuario_nombre, u.apellido AS usuario_apellido
           FROM resenas r
           JOIN libros l ON l.id = r.libro_id
           JOIN usuarios u ON u.id = r.usuario_id
           ORDER BY r.id"""
    )
    return [_serialize_review(row) for row in rows]


def get_review(review_id):
    row = _get_review_row(review_id)
    if row is None:
        raise NotFoundError("Reseña")
    return _serialize_review(row)


def create_review(data):
    if fetch_one("SELECT id FROM libros WHERE id = %s", (data["libro_id"],)) is None:
        raise NotFoundError("Libro")
    if fetch_one("SELECT id FROM usuarios WHERE id = %s", (data["usuario_id"],)) is None:
        raise NotFoundError("Usuario")

    row = fetch_value(
        """INSERT INTO resenas (libro_id, usuario_id, calificacion, comentario)
           VALUES (%s, %s, %s, %s)
           RETURNING id""",
        (data["libro_id"], data["usuario_id"], data["calificacion"], data["comentario"]),
    )
    return get_review(row["id"])


def update_review(review_id, data):
    if _get_review_row(review_id) is None:
        raise NotFoundError("Reseña")

    sets = []
    params = []
    if "calificacion" in data:
        sets.append("calificacion = %s")
        params.append(data["calificacion"])
    if "comentario" in data:
        sets.append("comentario = %s")
        params.append(data["comentario"])
    if sets:
        params.append(review_id)
        execute(f"UPDATE resenas SET {', '.join(sets)} WHERE id = %s", params)

    return get_review(review_id)


def delete_review(review_id):
    if _get_review_row(review_id) is None:
        raise NotFoundError("Reseña")
    execute("DELETE FROM resenas WHERE id = %s", (review_id,))