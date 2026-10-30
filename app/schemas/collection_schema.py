from app.errors.exceptions import ValidationError
from app.schemas.common import check_id_field, ensure_dict

MAX_NOMBRE = 100


def validate_collection(data):
    ensure_dict(data)
    errors = []

    nombre = data.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        errors.append("nombre es requerido")
    elif len(nombre.strip()) > MAX_NOMBRE:
        errors.append(f"nombre no puede superar los {MAX_NOMBRE} caracteres")

    if errors:
        raise ValidationError(errors)

    return {"nombre": nombre.strip()}


def validate_collection_book(data):
    ensure_dict(data)
    errors = []

    libro_id = data.get("libro_id")
    check_id_field(libro_id, "libro_id", errors, required=True)

    if errors:
        raise ValidationError(errors)

    return {"libro_id": libro_id}
