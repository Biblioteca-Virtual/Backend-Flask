from flask import Blueprint, jsonify, request

from app.schemas.user_schema import validate_login, validate_register
from app.services.user_service import login, register

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