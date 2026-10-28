from app.db import execute, fetch_all, fetch_one, fetch_value
from app.errors.exceptions import NotFoundError, ValidationError
from app.models.book import Libro

_QUERY_AUTORES_BY_LIBRO = """SELECT a.id, a.nombre, a.apellido
    FROM libros_autores la
    JOIN autores a ON a.id = la.autor_id
    WHERE la.libro_id = %s"""

_QUERY_LIBRO_BY_ID = """SELECT l.*, COALESCE(c.nombre, 'General') AS categoria_nombre
    FROM libros l
    LEFT JOIN categorias c ON c.id = l.categoria_id
    WHERE l.id = %s"""

_QUERY_LIBROS_LIST = """SELECT l.*, COALESCE(c.nombre, 'General') AS categoria_nombre
    FROM libros l
    LEFT JOIN categorias c ON c.id = l.categoria_id
    WHERE %s IS NULL OR LOWER(l.titulo) LIKE LOWER(%s)
    ORDER BY l.id"""

_UPDATE_LIBRO_STATIC = """UPDATE libros
    SET titulo = COALESCE(%s, titulo),
        isbn = CASE WHEN %s THEN %s ELSE isbn END,
        descripcion = CASE WHEN %s THEN %s ELSE descripcion END,
        anio_publicacion = CASE WHEN %s THEN %s ELSE anio_publicacion END,
        cantidad = COALESCE(%s, cantidad),
        categoria_id = COALESCE(%s, categoria_id),
        paginas_totales = CASE WHEN %s THEN %s ELSE paginas_totales END,
        paginas_leidas = CASE WHEN %s THEN %s ELSE paginas_leidas END,
        imagen_portada = CASE WHEN %s THEN %s ELSE imagen_portada END
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


def list_categories():
    rows = fetch_all("SELECT id, nombre, descripcion FROM categorias ORDER BY id")
    return [dict(row) for row in rows]


def _ensure_categoria(categoria_id):
    if not categoria_id:
        return 1
    row = fetch_one("SELECT id FROM categorias WHERE id = %s", (categoria_id,))
    if row is None:
        # Si la categoría especificada no existe, intentamos usar o crear la categoría 1 por defecto
        default_cat = fetch_one("SELECT id FROM categorias WHERE id = 1")
        if default_cat is None:
            execute("INSERT INTO categorias (id, nombre, descripcion) VALUES (1, 'General', 'Libros generales') ON CONFLICT DO NOTHING")
        return 1
    return categoria_id


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
            "INSERT INTO libros_autores (libro_id, autor_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
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
    cat_id = _ensure_categoria(data.get("categoria_id"))
    _ensure_autores(data.get("autores", []))

    row = fetch_value(
        """INSERT INTO libros
           (titulo, isbn, descripcion, anio_publicacion, cantidad, categoria_id,
            paginas_totales, paginas_leidas, imagen_portada)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (
            data["titulo"],
            data["isbn"],
            data["descripcion"],
            data["anio_publicacion"],
            data["cantidad"],
            cat_id,
            data.get("paginas_totales", 0),
            data.get("paginas_leidas", 0),
            data.get("imagen_portada"),
        ),
    )
    _add_autores(row["id"], data.get("autores", []))
    return get_book(row["id"])


def _update_book_fields(book_id, data):
    fields = (
        "titulo",
        "isbn",
        "descripcion",
        "anio_publicacion",
        "cantidad",
        "categoria_id",
        "paginas_totales",
        "paginas_leidas",
        "imagen_portada",
    )
    if any(k in data for k in fields):
        cat_id = data.get("categoria_id")
        if cat_id is not None:
            cat_id = _ensure_categoria(cat_id)

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
                cat_id,
                "paginas_totales" in data,
                data.get("paginas_totales"),
                "paginas_leidas" in data,
                data.get("paginas_leidas"),
                "imagen_portada" in data,
                data.get("imagen_portada"),
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


def update_book_progress(book_id, data):
    if _get_libro_row(book_id) is None:
        raise NotFoundError("Libro")

    set_clauses = []
    params = []
    if "paginas_totales" in data:
        set_clauses.append("paginas_totales = %s")
        params.append(data["paginas_totales"])
    if "paginas_leidas" in data:
        set_clauses.append("paginas_leidas = %s")
        params.append(data["paginas_leidas"])

    if set_clauses:
        params.append(book_id)
        sql = f"UPDATE libros SET {', '.join(set_clauses)} WHERE id = %s"
        execute(sql, tuple(params))

    return get_book(book_id)


def delete_book(book_id):
    row = _get_libro_row(book_id)
    if row is None:
        raise NotFoundError("Libro")
    execute("DELETE FROM libros WHERE id = %s", (book_id,))
    return row
