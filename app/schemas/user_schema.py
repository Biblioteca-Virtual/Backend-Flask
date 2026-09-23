import re

from app.errors.exceptions import ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_register(data):
    errors = []
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    nombre = data.get("nombre")
    apellido = data.get("apellido")
    email = data.get("email")
    password = data.get("password")

    if not nombre or not str(nombre).strip():
        errors.append("nombre es requerido")
    if not apellido or not str(apellido).strip():
        errors.append("apellido es requerido")
    if not email or not str(email).strip():
        errors.append("email es requerido")
    elif not EMAIL_RE.match(str(email)):
        errors.append("email no tiene un formato válido")
    if not password or len(str(password)) < 6:
        errors.append("password debe tener al menos 6 caracteres")

    if errors:
        raise ValidationError(errors)

    return {
        "nombre": str(nombre).strip(),
        "apellido": str(apellido).strip(),
        "email": str(email).strip().lower(),
        "password": str(password),
    }


def validate_login(data):
    errors = []
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    email = data.get("email")
    password = data.get("password")

    if not email:
        errors.append("email es requerido")
    if not password:
        errors.append("password es requerido")

    if errors:
        raise ValidationError(errors)

    return {
        "email": str(email).strip().lower(),
        "password": str(password),
    }