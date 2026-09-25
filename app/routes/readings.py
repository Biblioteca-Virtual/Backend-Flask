from flask import Blueprint, g, jsonify, request

from app.schemas.reading_schema import (
    validate_create_reading,
    validate_reading_filters,
    validate_update_reading,
)
from app.security import login_required
from app.services.reading_service import (
    create_reading,
    delete_reading,
    get_reading,
    list_readings,
    update_reading,
)

readings_bp = Blueprint("readings", __name__)


@readings_bp.get("/", strict_slashes=False)
@login_required
def get_readings():
    filters = validate_reading_filters(request.args)
    lecturas = list_readings(g.usuario_id, **filters)
    return jsonify({"data": lecturas}), 200


@readings_bp.get("/<int:reading_id>")
@login_required
def get_reading_by_id(reading_id):
    return jsonify({"data": get_reading(reading_id, g.usuario_id)}), 200


@readings_bp.post("/", strict_slashes=False)
@login_required
def post_reading():
    data = request.get_json(silent=True)
    validated = validate_create_reading(data)
    lectura = create_reading(validated, g.usuario_id)
    return jsonify({"data": lectura}), 201


@readings_bp.put("/<int:reading_id>")
@login_required
def put_reading(reading_id):
    data = request.get_json(silent=True)
    validated = validate_update_reading(data)
    lectura = update_reading(reading_id, validated, g.usuario_id)
    return jsonify({"data": lectura}), 200


@readings_bp.delete("/<int:reading_id>")
@login_required
def delete_reading_by_id(reading_id):
    delete_reading(reading_id, g.usuario_id)
    return jsonify({"message": "Lectura eliminada"}), 200
