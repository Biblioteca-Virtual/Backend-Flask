from app.errors.exceptions import ValidationError


def validate_create_review(data):
    errors = []
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    libro_id = data.get("libro_id")
    usuario_id = data.get("usuario_id")
    calificacion = data.get("calificacion")

    if libro_id is None:
        errors.append("libro_id es requerido")
    elif isinstance(libro_id, bool) or not isinstance(libro_id, int):
        errors.append("libro_id debe ser un número entero")

    if usuario_id is None:
        errors.append("usuario_id es requerido")
    elif isinstance(usuario_id, bool) or not isinstance(usuario_id, int):
        errors.append("usuario_id debe ser un número entero")

    if calificacion is None:
        errors.append("calificacion es requerida")
    elif (
        isinstance(calificacion, bool)
        or not isinstance(calificacion, int)
        or not 1 <= calificacion <= 5
    ):
        errors.append("calificacion debe ser un entero entre 1 y 5")

    if errors:
        raise ValidationError(errors)

    return {
        "libro_id": libro_id,
        "usuario_id": usuario_id,
        "calificacion": calificacion,
        "comentario": data.get("comentario"),
    }


def validate_update_review(data):
    errors = []
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    calificacion = data.get("calificacion")
    if calificacion is not None and (
        isinstance(calificacion, bool)
        or not isinstance(calificacion, int)
        or not 1 <= calificacion <= 5
    ):
        errors.append("calificacion debe ser un entero entre 1 y 5")

    if errors:
        raise ValidationError(errors)

    result = {}
    if calificacion is not None:
        result["calificacion"] = calificacion
    if "comentario" in data:
        result["comentario"] = data.get("comentario")
    return result