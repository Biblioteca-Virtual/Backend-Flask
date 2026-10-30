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

books_bp = Blueprint("books", __name__)


@books_bp.get("/")
@login_required
def get_books():
    search = request.args.get("q")
    return jsonify({"data": list_books(g.usuario_id, search=search)}), 200


@books_bp.get("/categories")
@login_required
def get_categories():
    return jsonify({"data": list_categories()}), 200


@books_bp.post("/categories")
@login_required
def post_category():
    data = request.get_json(silent=True)
    categoria, created = create_category(validate_category(data))
    return jsonify({"data": categoria}), 201 if created else 200


@books_bp.get("/authors")
@login_required
def get_authors():
    return jsonify({"data": list_authors()}), 200


@books_bp.post("/authors")
@login_required
def post_author():
    data = request.get_json(silent=True)
    autor, created = create_author(validate_author(data))
    return jsonify({"data": autor}), 201 if created else 200


@books_bp.get("/<int:book_id>")
@login_required
def get_book_by_id(book_id):
    return jsonify({"data": get_book(book_id, g.usuario_id)}), 200


@books_bp.get("/<int:book_id>/reviews")
@login_required
def get_book_reviews(book_id):
    return jsonify({"data": list_book_reviews(book_id, g.usuario_id)}), 200


@books_bp.post("/")
@login_required
def post_book():
    data = request.get_json(silent=True)
    validated = validate_create_book(data)
    libro = create_book(validated, g.usuario_id)
    return jsonify({"data": libro}), 201


@books_bp.put("/<int:book_id>")
@login_required
def put_book(book_id):
    data = request.get_json(silent=True)
    current = get_book(book_id, g.usuario_id)
    validated = validate_update_book(data, current["ubicacion"], current["url_lectura"])
    libro = update_book(book_id, validated, g.usuario_id)
    return jsonify({"data": libro}), 200


@books_bp.patch("/<int:book_id>/progress")
@login_required
def patch_book_progress(book_id):
    data = request.get_json(silent=True)
    validated = validate_update_progress(data)
    libro = update_book_progress(book_id, validated, g.usuario_id)
    return jsonify({"data": libro}), 200


@books_bp.delete("/<int:book_id>")
@login_required
def delete_book_by_id(book_id):
    delete_book(book_id, g.usuario_id)
    return jsonify({"message": "Libro eliminado"}), 200
