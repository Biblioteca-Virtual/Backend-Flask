from flask import Blueprint, g, jsonify, request

from app.schemas.collection_schema import validate_collection, validate_collection_book
from app.security import login_required
from app.services.collection_service import (
    add_book_to_collection,
    create_collection,
    delete_collection,
    get_collection,
    list_collections,
    remove_book_from_collection,
    rename_collection,
)

collections_bp = Blueprint("collections", __name__)


@collections_bp.get("/", strict_slashes=False)
@login_required
def get_collections():
    return jsonify({"data": list_collections(g.usuario_id)}), 200


@collections_bp.get("/<int:collection_id>")
@login_required
def get_collection_by_id(collection_id):
    return jsonify({"data": get_collection(collection_id, g.usuario_id)}), 200


@collections_bp.post("/", strict_slashes=False)
@login_required
def post_collection():
    data = request.get_json(silent=True)
    validated = validate_collection(data)
    coleccion = create_collection(validated, g.usuario_id)
    return jsonify({"data": coleccion}), 201


@collections_bp.put("/<int:collection_id>")
@collections_bp.patch("/<int:collection_id>")
@login_required
def put_collection(collection_id):
    data = request.get_json(silent=True)
    validated = validate_collection(data)
    coleccion = rename_collection(collection_id, validated, g.usuario_id)
    return jsonify({"data": coleccion}), 200


@collections_bp.delete("/<int:collection_id>")
@login_required
def delete_collection_by_id(collection_id):
    delete_collection(collection_id, g.usuario_id)
    return jsonify({"message": "Colección eliminada"}), 200


@collections_bp.post("/<int:collection_id>/books")
@login_required
def post_collection_book(collection_id):
    data = request.get_json(silent=True)
    validated = validate_collection_book(data)
    coleccion = add_book_to_collection(collection_id, validated["libro_id"], g.usuario_id)
    return jsonify({"data": coleccion}), 200


@collections_bp.delete("/<int:collection_id>/books/<int:book_id>")
@login_required
def delete_collection_book(collection_id, book_id):
    coleccion = remove_book_from_collection(collection_id, book_id, g.usuario_id)
    return jsonify({"data": coleccion}), 200
