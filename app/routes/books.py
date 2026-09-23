from flask import Blueprint, jsonify, request

from app.schemas.book_schema import validate_create_book, validate_update_book
from app.security import login_required
from app.services.book_service import (
    create_book,
    delete_book,
    get_book,
    list_books,
    update_book,
)

books_bp = Blueprint("books", __name__)


@books_bp.get("/")
@login_required
def get_books():
    search = request.args.get("q")
    return jsonify({"data": list_books(search=search)}), 200


@books_bp.get("/<int:book_id>")
@login_required
def get_book_by_id(book_id):
    return jsonify({"data": get_book(book_id)}), 200


@books_bp.post("/")
@login_required
def post_book():
    data = request.get_json(silent=True)
    validated = validate_create_book(data)
    libro = create_book(validated)
    return jsonify({"data": libro}), 201


@books_bp.put("/<int:book_id>")
@login_required
def put_book(book_id):
    data = request.get_json(silent=True)
    validated = validate_update_book(data)
    libro = update_book(book_id, validated)
    return jsonify({"data": libro}), 200


@books_bp.delete("/<int:book_id>")
@login_required
def delete_book_by_id(book_id):
    delete_book(book_id)
    return jsonify({"message": "Libro eliminado"}), 200