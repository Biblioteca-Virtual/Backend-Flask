from app.db import execute, fetch_all, fetch_one, fetch_value
from app.errors.exceptions import NotFoundError, ValidationError
from app.models.book import Libro

_QUERY_AUTORES_BY_LIBRO = """SELECT a.id, a.nombre, a.apellido
    FROM libros_autores la
    JOIN autores a ON a.id = la.autor_id
    WHERE la.libro_id = %s"""

_QUERY_LIBRO_BY_ID = """SELECT l.*, c.nombre AS categoria_nombre
    FROM libros l
    JOIN categorias c ON c.id = l.categoria_id
    WHERE l.id = %s"""

_QUERY_LIBROS_LIST = """SELECT l.*, c.nombre AS categoria_nombre
    FROM libros l
    JOIN categorias c ON c.id = l.categoria_id
    WHERE %s IS NULL OR LOWER(l.titulo) LIKE LOWER(%s)
    ORDER BY l.id"""

_UPDATE_LIBRO_STATIC = """UPDATE libros
    SET titulo = COALESCE(%s, titulo),
        isbn = CASE WHEN %s THEN %s ELSE isbn END,
        descripcion = CASE WHEN %s THEN %s ELSE descripcion END,
        anio_publicacion = CASE WHEN %s THEN %s ELSE anio_publicacion END,
        cantidad = COALESCE(%s, cantidad),
        categoria_id = COALESCE(%s, categoria_id)
    WHERE id = %s"""


def _fetch_autores(libro_id):
    rows = fetch_all(_QUERY_AUTORES_BY_LIBRO, (libro_id,))
    return [dict(row) for row in rows]


def _get_libro_row(libro_id):
    return fetch_one(_QUERY_LIBRO_BY_ID, (libro_id,))


def _serialize_libro(row):
    libro = Libro.from_row(row)
    libro.autores = _fetch_autores(libro.id)
    return libro.to_dict()


def _ensure_categoria(categoria_id):
    if fetch_one("SELECT id FROM categorias WHERE id = %s", (categoria_id,)) is None:
        raise ValidationError(["categoria_id no existe"])


def _ensure_autores(autores):
    if not autores:
        return
    rows = fetch_all("SELECT id FROM autores WHERE id = ANY(%s)", (autores,))
    found = {row["id"] for row in rows}
    missing = [autor_id for autor_id in autores if autor_id not in found]
    if missing:
        raise ValidationError([f"autores no existen: {missing}"])


def _add_autores(libro_id, autores):
    for autor_id in autores:
        execute(
            "INSERT INTO libros_autores (libro_id, autor_id) VALUES (%s, %s)",
            (libro_id, autor_id),
        )


def list_books(search=None):
    parameter = f"%{search}%" if search else None
    rows = fetch_all(_QUERY_LIBROS_LIST, (parameter, parameter))
    return [_serialize_libro(row) for row in rows]


def get_book(book_id):
    row = _get_libro_row(book_id)
    if row is None:
        raise NotFoundError("Libro")
    return _serialize_libro(row)


def create_book(data):
    _ensure_categoria(data["categoria_id"])
    _ensure_autores(data["autores"])

    row = fetch_value(
        """INSERT INTO libros
           (titulo, isbn, descripcion, anio_publicacion, cantidad, categoria_id)
           VALUES (%s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (
            data["titulo"],
            data["isbn"],
            data["descripcion"],
            data["anio_publicacion"],
            data["cantidad"],
            data["categoria_id"],
        ),
    )
    _add_autores(row["id"], data["autores"])
    return get_book(row["id"])


def _update_book_fields(book_id, data):
    fields = ("titulo", "isbn", "descripcion", "anio_publicacion", "cantidad", "categoria_id")
    if any(k in data for k in fields):
        execute(
            _UPDATE_LIBRO_STATIC,
            (
                data.get("titulo"),
                "isbn" in data,
                data.get("isbn"),
                "descripcion" in data,
                data.get("descripcion"),
                "anio_publicacion" in data,
                data.get("anio_publicacion"),
                data.get("cantidad"),
                data.get("categoria_id"),
                book_id,
            ),
        )


def _update_book_autores(book_id, autores):
    execute("DELETE FROM libros_autores WHERE libro_id = %s", (book_id,))
    _ensure_autores(autores)
    _add_autores(book_id, autores)


def update_book(book_id, data):
    if _get_libro_row(book_id) is None:
        raise NotFoundError("Libro")

    _update_book_fields(book_id, data)
    if "autores" in data:
        _update_book_autores(book_id, data["autores"])

    return get_book(book_id)


def delete_book(book_id):
    row = _get_libro_row(book_id)
    if row is None:
        raise NotFoundError("Libro")
    execute("DELETE FROM libros WHERE id = %s", (book_id,))
    return row