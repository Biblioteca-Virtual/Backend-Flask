# Rutas de autenticación (/api/auth): registro, inicio de sesión con verificación
# por correo y datos del usuario actual.
from flask import Blueprint, g, jsonify, request

from app.schemas.user_schema import validate_login, validate_register, validate_secret
from app.security import login_required
from app.services import session_verification_service
from app.services.user_service import get_user, login, register

# Blueprint que agrupa estas rutas; create_app() lo registra con el prefijo /api/auth.
auth_bp = Blueprint("auth", __name__)


# POST /api/auth/register: crea una cuenta nueva y devuelve el usuario (sin contraseña).
@auth_bp.post("/register")
def register_user():
    data = request.get_json(silent=True)
    validated = validate_register(data)
    usuario = register(validated)
    return jsonify({"data": usuario}), 201


# POST /api/auth/login: comprueba email y contraseña. No devuelve el token todavía:
# primero hay que confirmar el inicio de sesión desde el correo.
@auth_bp.post("/login")
def login_user():
    """Contraseña correcta: 202 y se manda el correo de "Verificar Sesión"."""
    data = request.get_json(silent=True)
    validated = validate_login(data)
    return jsonify({"data": login(validated)}), 202


# POST /api/auth/verify-session: recibe el token del link del correo.
@auth_bp.post("/verify-session")
def verify_session():
    """Botón "Verificar Sesión" del correo: verifica y devuelve la sesión."""
    token = validate_secret(request.get_json(silent=True), "token")
    return jsonify({"data": session_verification_service.verify(token)}), 200


# POST /api/auth/session-status: 200 cuando la sesión ya se verificó (con el token
# JWT) y 202 mientras siga pendiente.
@auth_bp.post("/session-status")
def session_status():
    """La pestaña del login pregunta si ya se tocó el botón del correo."""
    consulta = validate_secret(request.get_json(silent=True), "consulta")
    result = session_verification_service.check(consulta)
    status = 200 if result["estado"] == "verificada" else 202
    return jsonify({"data": result}), status


# POST /api/auth/resend-session-email: vuelve a mandar el correo de verificación.
@auth_bp.post("/resend-session-email")
def resend_session_email():
    consulta = validate_secret(request.get_json(silent=True), "consulta")
    return jsonify({"data": session_verification_service.resend(consulta)}), 200


# GET /api/auth/me: datos del usuario dueño del token.
@auth_bp.get("/me")
@login_required
def get_me():
    return jsonify({"data": get_user(g.usuario_id)}), 200
