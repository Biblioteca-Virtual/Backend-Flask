from flask import Blueprint, g, jsonify, request

from app.schemas.user_schema import validate_login, validate_register
from app.security import login_required
from app.services.user_service import get_user, login, register

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register_user():
    data = request.get_json(silent=True)
    validated = validate_register(data)
    usuario = register(validated)
    return jsonify({"data": usuario}), 201


@auth_bp.post("/login")
def login_user():
    data = request.get_json(silent=True)
    validated = validate_login(data)
    result = login(validated)
    return jsonify({"data": result}), 200


@auth_bp.get("/me")
@login_required
def get_me():
    return jsonify({"data": get_user(g.usuario_id)}), 200