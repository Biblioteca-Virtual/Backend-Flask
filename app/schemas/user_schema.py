import re

from app.errors.exceptions import ValidationError
from app.schemas.common import check_required_text, ensure_dict

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_email_format(email, errors):
    if not email or not str(email).strip():
        errors.append("email es requerido")
    elif not EMAIL_RE.match(str(email)):
        errors.append("email no tiene un formato válido")


def _check_password_length(password, errors, min_len=6):
    if not password:
        errors.append("password es requerido")
    elif len(str(password)) < min_len:
        errors.append(f"password debe tener al menos {min_len} caracteres")


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