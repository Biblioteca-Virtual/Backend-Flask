from app.errors.exceptions import ValidationError

ESTADOS = {"activo", "devuelto"}


def validate_create_reading(data):
    errors = []
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    usuario_id = data.get("usuario_id")
    libro_id = data.get("libro_id")

    if usuario_id is None:
        errors.append("usuario_id es requerido")
    elif isinstance(usuario_id, bool) or not isinstance(usuario_id, int):
        errors.append("usuario_id debe ser un número entero")

    if libro_id is None:
        errors.append("libro_id es requerido")
    elif isinstance(libro_id, bool) or not isinstance(libro_id, int):
        errors.append("libro_id debe ser un número entero")

    if errors:
        raise ValidationError(errors)
    return {"usuario_id": usuario_id, "libro_id": libro_id}


def validate_update_reading(data):
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    estado = data.get("estado")
    if estado not in ESTADOS:
        raise ValidationError(
            [f"estado debe ser uno de los siguientes valores: {', '.join(sorted(ESTADOS))}"]
        )
    return {"estado": estado}