# Rutas de libros (/api/books). Todas exigen sesión iniciada: cada usuario ve y
# modifica solo sus propios libros. También expone las categorías y los autores.
from flask import Blueprint, g, jsonify, request

from app.schemas.book_schema import (
    validate_author,
    validate_category,
    validate_create_book,
    validate_update_book,
    validate_update_progress,
)
from app.security import login_required
from app.services.book_service import (
    create_author,
    create_book,
    create_category,
    delete_book,
    get_book,
    list_authors,
    list_book_reviews,
    list_books,
    list_categories,
    update_book,
    update_book_progress,
)

# Blueprint que agrupa estas rutas; create_app() lo registra con el prefijo /api/books.
books_bp = Blueprint("books", __name__)


# GET /api/books?q=texto: lista los libros del usuario; con q filtra por título (sin importar mayúsculas).
@books_bp.get("/")
@login_required
def get_books():
    search = request.args.get("q")
    return jsonify({"data": list_books(g.usuario_id, search=search)}), 200


# GET /api/books/categories: todas las categorías disponibles.
@books_bp.get("/categories")
@login_required
def get_categories():
    return jsonify({"data": list_categories()}), 200


# POST /api/books/categories: crea una categoría. Si ya existía, la devuelve con 200
# en lugar de 201, así el frontend no tiene que tratar el duplicado como error.
@books_bp.post("/categories")
@login_required
def post_category():
    data = request.get_json(silent=True)
    categoria, created = create_category(validate_category(data))
    return jsonify({"data": categoria}), 201 if created else 200


# GET /api/books/authors: todos los autores cargados.
@books_bp.get("/authors")
@login_required
def get_authors():
    return jsonify({"data": list_authors()}), 200


# POST /api/books/authors: crea un autor; si ya existía, lo devuelve con 200.
@books_bp.post("/authors")
@login_required
def post_author():
    data = request.get_json(silent=True)
    autor, created = create_author(validate_author(data))
    return jsonify({"data": autor}), 201 if created else 200


# GET /api/books/<id>: detalle de un libro del usuario (404 si no es suyo o no existe).
@books_bp.get("/<int:book_id>")
@login_required
def get_book_by_id(book_id):
    return jsonify({"data": get_book(book_id, g.usuario_id)}), 200


# GET /api/books/<id>/reviews: reseñas de la comunidad sobre ese libro.
@books_bp.get("/<int:book_id>/reviews")
@login_required
def get_book_reviews(book_id):
    return jsonify({"data": list_book_reviews(book_id, g.usuario_id)}), 200


# POST /api/books: crea un libro en la biblioteca del usuario.
@books_bp.post("/")
@login_required
def post_book():
    data = request.get_json(silent=True)
    validated = validate_create_book(data)
    libro = create_book(validated, g.usuario_id)
    return jsonify({"data": libro}), 201


# PUT /api/books/<id>: edita un libro. Primero lee el libro actual porque la URL de
# lectura se valida contra la ubicación que va a quedar guardada.
@books_bp.put("/<int:book_id>")
@login_required
def put_book(book_id):
    data = request.get_json(silent=True)
    current = get_book(book_id, g.usuario_id)
    validated = validate_update_book(data, current["ubicacion"], current["url_lectura"])
    libro = update_book(book_id, validated, g.usuario_id)
    return jsonify({"data": libro}), 200


# PATCH /api/books/<id>/progress: actualiza solo las páginas totales o leídas.
@books_bp.patch("/<int:book_id>/progress")
@login_required
def patch_book_progress(book_id):
    data = request.get_json(silent=True)
    validated = validate_update_progress(data)
    libro = update_book_progress(book_id, validated, g.usuario_id)
    return jsonify({"data": libro}), 200


# DELETE /api/books/<id>: borra un libro del usuario.
@books_bp.delete("/<int:book_id>")
@login_required
def delete_book_by_id(book_id):
    delete_book(book_id, g.usuario_id)
    return jsonify({"message": "Libro eliminado"}), 200
