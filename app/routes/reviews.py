from flask import Blueprint, jsonify, request

from app.schemas.review_schema import validate_create_review, validate_update_review
from app.security import login_required
from app.services.review_service import (
    create_review,
    delete_review,
    get_review,
    list_reviews,
    update_review,
)

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.get("/")
@login_required
def get_reviews():
    return jsonify({"data": list_reviews()}), 200


@reviews_bp.get("/<int:review_id>")
@login_required
def get_review_by_id(review_id):
    return jsonify({"data": get_review(review_id)}), 200


@reviews_bp.post("/")
@login_required
def post_review():
    data = request.get_json(silent=True)
    validated = validate_create_review(data)
    resena = create_review(validated)
    return jsonify({"data": resena}), 201


@reviews_bp.put("/<int:review_id>")
@login_required
def put_review(review_id):
    data = request.get_json(silent=True)
    validated = validate_update_review(data)
    resena = update_review(review_id, validated)
    return jsonify({"data": resena}), 200


@reviews_bp.delete("/<int:review_id>")
@login_required
def delete_review_by_id(review_id):
    delete_review(review_id)
    return jsonify({"message": "Reseña eliminada"}), 200