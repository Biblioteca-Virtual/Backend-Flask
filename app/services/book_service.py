from app.db import execute, fetch_all, fetch_one, fetch_value
from app.errors.exceptions import NotFoundError, ValidationError
from app.models.book import Libro
from app.models.review import Resena
from app.services.title_match import same_book

_QUERY_AUTORES_BY_LIBRO = """SELECT a.id, a.nombre, a.apellido
    FROM libros_autores la
    JOIN autores a ON a.id = la.autor_id
    WHERE la.libro_id = %s"""

# Todas las consultas de libros van acotadas al dueño: un libro ajeno es 404.
_QUERY_LIBRO_BY_ID = """SELECT l.*, COALESCE(c.nombre, 'General') AS categoria_nombre
    FROM libros l
    LEFT JOIN categorias c ON c.id = l.categoria_id
    WHERE l.id = %s AND l.usuario_id = %s"""

_QUERY_LIBROS_LIST = """SELECT l.*, COALESCE(c.nombre, 'General') AS categoria_nombre
    FROM libros l
    LEFT JOIN categorias c ON c.id = l.categoria_id
    WHERE l.usuario_id = %s
      AND (%s IS NULL OR LOWER(l.titulo) LIKE LOWER(%s))
    ORDER BY l.id"""

_UPDATE_LIBRO_STATIC = """UPDATE libros
    SET titulo = COALESCE(%s, titulo),
        descripcion = CASE WHEN %s THEN %s ELSE descripcion END,
        categoria_id = COALESCE(%s, categoria_id),
        paginas_totales = CASE WHEN %s THEN %s ELSE paginas_totales END,
        paginas_leidas = CASE WHEN %s THEN %s ELSE paginas_leidas END,
        imagen_portada = CASE WHEN %s THEN %s ELSE imagen_portada END,
        ubicacion = COALESCE(%s, ubicacion),
        url_lectura = CASE WHEN %s THEN %s ELSE url_lectura END
    WHERE id = %s AND usuario_id = %s"""

_QUERY_REVIEWS_BY_LIBROS = """SELECT r.*, l.titulo AS libro_titulo,
                                     u.nombre AS usuario_nombre,
                                     u.apellido AS usuario_apellido
    FROM resenas r
    JOIN libros l ON l.id = r.libro_id
    JOIN usuarios u ON u.id = r.usuario_id
    WHERE r.libro_id = ANY(%s)
    ORDER BY r.fecha_creacion DESC, r.id DESC"""

_UPDATE_FIELDS = (
    "titulo",
    "descripcion",
    "categoria_id",
    "paginas_totales",
    "paginas_leidas",
    "imagen_portada",
    "ubicacion",
    "url_lectura",
)


def _fetch_autores(libro_id):
    rows = fetch_all(_QUERY_AUTORES_BY_LIBRO, (libro_id,))
    return [dict(row) for row in rows]


def _get_libro_row(libro_id, usuario_id):
    return fetch_one(_QUERY_LIBRO_BY_ID, (libro_id, usuario_id))


def _serialize_libro(row):
    libro = Libro.from_row(row)
    libro.autores = _fetch_autores(libro.id)
    return libro.to_dict()


def list_categories():
    rows = fetch_all("SELECT id, nombre, descripcion FROM categorias ORDER BY nombre")
    return [dict(row) for row in rows]


def create_category(data):
    """Crea una categoría compartida. Si ya existe (sin importar mayúsculas), la devuelve.

    Returns:
        (categoria, creada): la categoría y si se creó en esta llamada.
    """
    existing = fetch_one(
        "SELECT id, nombre, descripcion FROM categorias WHERE LOWER(nombre) = LOWER(%s)",
        (data["nombre"],),
    )
    if existing is not None:
        return dict(existing), False
    row = fetch_value(
        """INSERT INTO categorias (nombre) VALUES (%s)
           RETURNING id, nombre, descripcion""",
        (data["nombre"],),
    )
    return dict(row), True


def list_authors():
    rows = fetch_all("SELECT id, nombre, apellido FROM autores ORDER BY apellido, nombre")
    return [dict(row) for row in rows]


def create_author(data):
    """Crea un autor compartido a partir del nombre completo, o devuelve el que ya existe.

    Se compara el nombre completo sin importar mayúsculas, así "Jorge Luis Borges"
    encuentra al autor guardado como nombre "Jorge Luis" y apellido "Borges".

    Returns:
        (autor, creado): el autor y si se creó en esta llamada.
    """
    completo = data["nombre_completo"]
    existing = fetch_one(
        """SELECT id, nombre, apellido FROM autores
           WHERE LOWER(TRIM(nombre || ' ' || apellido)) = LOWER(%s)""",
        (completo,),
    )
    if existing is not None:
        return dict(existing), False
    # Si se escribió todo en minúsculas se guarda con mayúscula inicial.
    if completo == completo.lower():
        completo = " ".join(word[:1].upper() + word[1:] for word in completo.split(" "))
    # Primera palabra como nombre y el resto como apellido.
    nombre, _, apellido = completo.partition(" ")
    row = fetch_value(
        """INSERT INTO autores (nombre, apellido) VALUES (%s, %s)
           RETURNING id, nombre, apellido""",
        (nombre, apellido.strip()),
    )
    return dict(row), True


def _ensure_categoria(categoria_id):
    if not categoria_id:
        return 1
    row = fetch_one("SELECT id FROM categorias WHERE id = %s", (categoria_id,))
    if row is None:
        raise ValidationError([f"La categoría {categoria_id} no existe"])
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


def list_books(usuario_id, search=None):
    parameter = f"%{search}%" if search else None
    rows = fetch_all(_QUERY_LIBROS_LIST, (usuario_id, parameter, parameter))
    return [_serialize_libro(row) for row in rows]


def get_book(book_id, usuario_id):
    row = _get_libro_row(book_id, usuario_id)
    if row is None:
        raise NotFoundError("Libro")
    return _serialize_libro(row)


def create_book(data, usuario_id):
    cat_id = _ensure_categoria(data.get("categoria_id"))
    _ensure_autores(data.get("autores", []))

    row = fetch_value(
        """INSERT INTO libros
           (usuario_id, titulo, descripcion, categoria_id, paginas_totales,
            paginas_leidas, imagen_portada, ubicacion, url_lectura)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (
            usuario_id,
            data["titulo"],
            data["descripcion"],
            cat_id,
            data.get("paginas_totales", 0),
            data.get("paginas_leidas", 0),
            data.get("imagen_portada"),
            data.get("ubicacion", "fisico"),
            data.get("url_lectura"),
        ),
    )
    _add_autores(row["id"], data.get("autores", []))
    return get_book(row["id"], usuario_id)


def _update_book_fields(book_id, data, usuario_id):
    if not any(k in data for k in _UPDATE_FIELDS):
        return
    cat_id = data.get("categoria_id")
    if cat_id is not None:
        cat_id = _ensure_categoria(cat_id)

    execute(
        _UPDATE_LIBRO_STATIC,
        (
            data.get("titulo"),
            "descripcion" in data,
            data.get("descripcion"),
            cat_id,
            "paginas_totales" in data,
            data.get("paginas_totales"),
            "paginas_leidas" in data,
            data.get("paginas_leidas"),
            "imagen_portada" in data,
            data.get("imagen_portada"),
            data.get("ubicacion"),
            "url_lectura" in data,
            data.get("url_lectura"),
            book_id,
            usuario_id,
        ),
    )


def _update_book_autores(book_id, autores):
    execute("DELETE FROM libros_autores WHERE libro_id = %s", (book_id,))
    _ensure_autores(autores)
    _add_autores(book_id, autores)


def update_book(book_id, data, usuario_id):
    if _get_libro_row(book_id, usuario_id) is None:
        raise NotFoundError("Libro")

    _update_book_fields(book_id, data, usuario_id)
    if "autores" in data:
        _update_book_autores(book_id, data["autores"])

    return get_book(book_id, usuario_id)


def update_book_progress(book_id, data, usuario_id):
    if _get_libro_row(book_id, usuario_id) is None:
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
        params.extend([book_id, usuario_id])
        sql = f"UPDATE libros SET {', '.join(set_clauses)} WHERE id = %s AND usuario_id = %s"
        execute(sql, tuple(params))

    return get_book(book_id, usuario_id)


def delete_book(book_id, usuario_id):
    row = _get_libro_row(book_id, usuario_id)
    if row is None:
        raise NotFoundError("Libro")
    execute("DELETE FROM libros WHERE id = %s AND usuario_id = %s", (book_id, usuario_id))
    return row


def list_book_reviews(book_id, usuario_id):
    """Reseñas de este libro y de los libros de otros usuarios con un título equivalente.

    Se comparan los títulos en Python (ver `title_match`): alcanza para una
    biblioteca escolar. Con muchos miles de libros convendría guardar el título
    normalizado e indexarlo con `pg_trgm`.
    """
    libro = get_book(book_id, usuario_id)
    candidates = fetch_all("SELECT id, titulo FROM libros")
    ids = [row["id"] for row in candidates if same_book(libro["titulo"], row["titulo"])]
    if book_id not in ids:
        ids.append(book_id)
    rows = fetch_all(_QUERY_REVIEWS_BY_LIBROS, (ids,))
    return [Resena.from_row(row).to_dict() for row in rows]
