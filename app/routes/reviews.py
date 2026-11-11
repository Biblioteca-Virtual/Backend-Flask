# Rutas de reseñas (/api/reviews). Todas exigen sesión iniciada; las reseñas se ven
# entre todos los usuarios, pero solo el autor puede editar o borrar la suya.
from flask import Blueprint, g, jsonify, request

from app.schemas.review_schema import validate_create_review, validate_update_review
from app.security import login_required
from app.services.review_service import (
    create_review,
    delete_review,
    get_review,
    list_reviews,
    update_review,
)

# Blueprint que agrupa estas rutas; create_app() lo registra con el prefijo /api/reviews.
reviews_bp = Blueprint("reviews", __name__)


# GET /api/reviews: todas las reseñas.
@reviews_bp.get("/", strict_slashes=False)
@login_required
def get_reviews():
    return jsonify({"data": list_reviews()}), 200


# GET /api/reviews/<id>: una reseña.
@reviews_bp.get("/<int:review_id>")
@login_required
def get_review_by_id(review_id):
    return jsonify({"data": get_review(review_id)}), 200


# POST /api/reviews: publica una reseña del usuario sobre uno de sus libros.
@reviews_bp.post("/", strict_slashes=False)
@login_required
def post_review():
    data = request.get_json(silent=True)
    validated = validate_create_review(data)
    resena = create_review(validated, g.usuario_id)
    return jsonify({"data": resena}), 201


# PUT /api/reviews/<id>: edita la calificación o el comentario de la reseña propia.
@reviews_bp.put("/<int:review_id>")
@login_required
def put_review(review_id):
    data = request.get_json(silent=True)
    validated = validate_update_review(data)
    resena = update_review(review_id, validated, g.usuario_id)
    return jsonify({"data": resena}), 200


# DELETE /api/reviews/<id>: borra la reseña propia.
@reviews_bp.delete("/<int:review_id>")
@login_required
def delete_review_by_id(review_id):
    delete_review(review_id, g.usuario_id)
    return jsonify({"message": "Reseña eliminada"}), 200
