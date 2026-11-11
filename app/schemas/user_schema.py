# Validación de los datos de registro, inicio de sesión y verificación por correo.
import re

from app.errors.exceptions import ValidationError
from app.schemas.common import check_required_text, ensure_dict

# Formato básico de email: algo@algo.algo, sin espacios.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# El email es obligatorio y tiene que tener un formato válido.
def _check_email_format(email, errors):
    if not email or not str(email).strip():
        errors.append("email es requerido")
    elif not EMAIL_RE.match(str(email)):
        errors.append("email no tiene un formato válido")


# La contraseña es obligatoria y tiene un largo mínimo (6 caracteres por defecto).
def _check_password_length(password, errors, min_len=6):
    if not password:
        errors.append("password es requerido")
    elif len(str(password)) < min_len:
        errors.append(f"password debe tener al menos {min_len} caracteres")


# Registro: nombre, apellido, email y contraseña. El email se guarda en minúsculas
# para que no haya dos cuentas que solo difieran en mayúsculas.
def validate_register(data):
    ensure_dict(data)
    errors = []

    nombre = check_required_text(data, "nombre", errors)
    apellido = check_required_text(data, "apellido", errors)
    _check_email_format(data.get("email"), errors)
    _check_password_length(data.get("password"), errors, min_len=6)

    if errors:
        raise ValidationError(errors)

    return {
        "nombre": nombre,
        "apellido": apellido,
        "email": str(data["email"]).strip().lower(),
        "password": str(data["password"]),
    }


def validate_secret(data, field):
    """Valida el `token` del link del correo o la `consulta` de la pestaña del login."""
    ensure_dict(data)
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError([f"{field} es requerido"])
    return value.strip()


# Inicio de sesión: solo exige que vengan email y contraseña. Si son correctos lo
# decide el servicio al compararlos con la base de datos.
def validate_login(data):
    ensure_dict(data)
    errors = []

    if not data.get("email"):
        errors.append("email es requerido")
    if not data.get("password"):
        errors.append("password es requerido")

    if errors:
        raise ValidationError(errors)

    return {
        "email": str(data["email"]).strip().lower(),
        "password": str(data["password"]),
    }
