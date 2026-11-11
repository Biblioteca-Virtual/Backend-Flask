# Seguridad: hash de contraseñas con Argon2 y autenticación con tokens JWT.
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from functools import wraps

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from werkzeug.security import check_password_hash as legacy_check_password_hash

from flask import g, request

from app.errors.exceptions import UnauthorizedError

# Un único hasher Argon2 con los parámetros por defecto de la librería.
_password_hasher = PasswordHasher()


# Devuelve el hash Argon2 de la contraseña (nunca se guarda la contraseña en texto plano).
def hash_password(password):
    return _password_hasher.hash(password)


# Comprueba la contraseña contra el hash guardado. Los usuarios viejos tienen hashes de
# Werkzeug, que se verifican con la función anterior; los nuevos usan Argon2.
def verify_password(stored_hash, password):
    if not stored_hash or not stored_hash.startswith("$argon2"):
        return legacy_check_password_hash(stored_hash, password)
    try:
        return _password_hasher.verify(stored_hash, password)
    except VerificationError:
        return False


# Indica si el hash es del formato viejo, para reemplazarlo por Argon2 en el próximo login.
def is_legacy_password_hash(stored_hash):
    return not stored_hash or not stored_hash.startswith("$argon2")


# Crea un token JWT firmado con SECRET_KEY. Guarda el id del usuario en "sub" y vence
# a las TOKEN_EXPIRATION_HOURS horas.
def create_token(usuario_id):
    from flask import current_app

    config = current_app.config
    payload = {
        "sub": str(usuario_id),
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=config["TOKEN_EXPIRATION_HOURS"]),
    }
    return pyjwt.encode(payload, config["SECRET_KEY"], algorithm="HS256")


# Valida la firma y el vencimiento del token y devuelve su contenido.
# Si está vencido o es inválido, responde 401 con un mensaje claro.
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


# Decorador para las rutas protegidas: exige un token válido y deja el id del usuario
# en `g.usuario_id` para que la ruta sepa quién hace el pedido.
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = _extract_token()
        payload = decode_token(token)
        g.usuario_id = int(payload["sub"])
        return view(*args, **kwargs)

    return wrapped


# Saca el token del encabezado "Authorization: Bearer <token>". Si falta, responde 401.
def _extract_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise UnauthorizedError("Se requiere token de autenticación")
    return auth[len("Bearer "):].strip()
