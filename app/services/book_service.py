# Lógica de negocio de libros, autores y categorías: consultas a la base de datos,
# controles de pertenencia y armado de las respuestas.
from app.db import execute, fetch_all, fetch_one, fetch_value
from app.errors.exceptions import NotFoundError, ValidationError
from app.models.book import Libro
from app.models.review import Resena
from app.services.title_match import same_book

# Autores de un libro (tabla intermedia libros_autores).
_QUERY_AUTORES_BY_LIBRO = """SELECT a.id, a.nombre, a.apellido
    FROM libros_autores la
    JOIN autores a ON a.id = la.autor_id
    WHERE la.libro_id = %s"""

# Todas las consultas de libros van acotadas al dueño: un libro ajeno es 404.
_QUERY_LIBRO_BY_ID = """SELECT l.*, COALESCE(c.nombre, 'General') AS categoria_nombre
    FROM libros l
    LEFT JOIN categorias c ON c.id = l.categoria_id
    WHERE l.id = %s AND l.usuario_id = %s"""

# Libros del usuario. Si el segundo parámetro es NULL no filtra; si no, busca el
# texto dentro del título sin importar mayúsculas.
_QUERY_LIBROS_LIST = """SELECT l.*, COALESCE(c.nombre, 'General') AS categoria_nombre
    FROM libros l
    LEFT JOIN categorias c ON c.id = l.categoria_id
    WHERE l.usuario_id = %s
      AND (%s IS NULL OR LOWER(l.titulo) LIKE LOWER(%s))
    ORDER BY l.id"""

# Actualización parcial con una sola consulta fija (sin armar SQL a mano):
# - COALESCE(%s, campo) deja el valor actual cuando llega NULL.
# - CASE WHEN %s THEN ... recibe un booleano "¿vino el campo?", así se puede
#   guardar NULL a propósito (por ejemplo, borrar la descripción).
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

# Cambia solo las páginas; la que llega como NULL conserva su valor.
_UPDATE_PROGRESO = """UPDATE libros
    SET paginas_totales = COALESCE(%s, paginas_totales),
        paginas_leidas = COALESCE(%s, paginas_leidas)
    WHERE id = %s AND usuario_id = %s"""

# Reseñas de varios libros a la vez (ANY recibe una lista de ids), las más nuevas primero.
_QUERY_REVIEWS_BY_LIBROS = """SELECT r.*, l.titulo AS libro_titulo,
                                     u.nombre AS usuario_nombre,
                                     u.apellido AS usuario_apellido
    FROM resenas r
    JOIN libros l ON l.id = r.libro_id
    JOIN usuarios u ON u.id = r.usuario_id
    WHERE r.libro_id = ANY(%s)
    ORDER BY r.fecha_creacion DESC, r.id DESC"""

# Campos que guarda _UPDATE_LIBRO_STATIC; los autores se actualizan aparte.
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


# Devuelve los autores del libro como lista de diccionarios.
def _fetch_autores(libro_id):
    rows = fetch_all(_QUERY_AUTORES_BY_LIBRO, (libro_id,))
    return [dict(row) for row in rows]


# Fila del libro solo si pertenece al usuario; si no, None.
def _get_libro_row(libro_id, usuario_id):
    return fetch_one(_QUERY_LIBRO_BY_ID, (libro_id, usuario_id))


# Convierte la fila en el JSON del libro, con sus autores incluidos.
def _serialize_libro(row):
    libro = Libro.from_row(row)
    libro.autores = _fetch_autores(libro.id)
    return libro.to_dict()


# Todas las categorías, ordenadas por nombre.
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


# Todos los autores, ordenados por apellido y nombre.
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


# Sin categoría usa la de id 1; si viene una, comprueba que exista (si no, 400).
def _ensure_categoria(categoria_id):
    if not categoria_id:
        return 1
    row = fetch_one("SELECT id FROM categorias WHERE id = %s", (categoria_id,))
    if row is None:
        raise ValidationError([f"La categoría {categoria_id} no existe"])
    return categoria_id


# Comprueba que existan todos los autores indicados; lista los que falten en el error.
def _ensure_autores(autores):
    if not autores:
        return
    rows = fetch_all("SELECT id FROM autores WHERE id = ANY(%s)", (autores,))
    found = {row["id"] for row in rows}
    missing = [autor_id for autor_id in autores if autor_id not in found]
    if missing:
        raise ValidationError([f"autores no existen: {missing}"])


# Vincula los autores al libro. ON CONFLICT DO NOTHING ignora los ya vinculados.
def _add_autores(libro_id, autores):
    for autor_id in autores:
        execute(
            "INSERT INTO libros_autores (libro_id, autor_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (libro_id, autor_id),
        )


# Libros del usuario; con `search` filtra por parte del título (los % son comodines).
def list_books(usuario_id, search=None):
    parameter = f"%{search}%" if search else None
    rows = fetch_all(_QUERY_LIBROS_LIST, (usuario_id, parameter, parameter))
    return [_serialize_libro(row) for row in rows]


# Un libro del usuario; 404 si no existe o es de otro usuario.
def get_book(book_id, usuario_id):
    row = _get_libro_row(book_id, usuario_id)
    if row is None:
        raise NotFoundError("Libro")
    return _serialize_libro(row)


# Crea el libro después de comprobar la categoría y los autores, y lo devuelve completo.
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


# Guarda los campos simples que llegaron (si no llegó ninguno, no hace nada).
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


# Reemplaza la lista de autores: borra los vínculos y crea los nuevos.
def _update_book_autores(book_id, autores):
    execute("DELETE FROM libros_autores WHERE libro_id = %s", (book_id,))
    _ensure_autores(autores)
    _add_autores(book_id, autores)


# Edita un libro del usuario (404 si no es suyo) y devuelve cómo quedó.
def update_book(book_id, data, usuario_id):
    if _get_libro_row(book_id, usuario_id) is None:
        raise NotFoundError("Libro")

    _update_book_fields(book_id, data, usuario_id)
    if "autores" in data:
        _update_book_autores(book_id, data["autores"])

    return get_book(book_id, usuario_id)


# Actualiza las páginas totales o leídas de un libro del usuario.
def update_book_progress(book_id, data, usuario_id):
    if _get_libro_row(book_id, usuario_id) is None:
        raise NotFoundError("Libro")

    execute(
        _UPDATE_PROGRESO,
        (data.get("paginas_totales"), data.get("paginas_leidas"), book_id, usuario_id),
    )
    return get_book(book_id, usuario_id)


# Borra un libro del usuario y devuelve la fila borrada (404 si no es suyo).
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
