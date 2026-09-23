import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from functools import wraps

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from werkzeug.security import check_password_hash as legacy_check_password_hash

from flask import g, request

from app.errors.exceptions import UnauthorizedError

_password_hasher = PasswordHasher()


def hash_password(password):
    return _password_hasher.hash(password)


def verify_password(stored_hash, password):
    if not stored_hash or not stored_hash.startswith("$argon2"):
        return legacy_check_password_hash(stored_hash, password)
    try:
        return _password_hasher.verify(stored_hash, password)
    except VerificationError:
        return False


def is_legacy_password_hash(stored_hash):
    return not stored_hash or not stored_hash.startswith("$argon2")


def create_token(usuario_id):
    from flask import current_app

    config = current_app.config
    payload = {
        "sub": str(usuario_id),
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=config["TOKEN_EXPIRATION_HOURS"]),
    }
    return pyjwt.encode(payload, config["SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    from flask import current_app

    config = current_app.config
    try:
        payload = pyjwt.decode(token, config["SECRET_KEY"], algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise UnauthorizedError("El token ha expirado")
    except pyjwt.InvalidTokenError:
        raise UnauthorizedError("Token inválido")
    return payload


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = _extract_token()
        payload = decode_token(token)
        g.usuario_id = int(payload["sub"])
        return view(*args, **kwargs)

    return wrapped


def _extract_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise UnauthorizedError("Se requiere token de autenticación")
    return auth[len("Bearer "):].strip()