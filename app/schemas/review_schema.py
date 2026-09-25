from app.errors.exceptions import ValidationError

MAX_INTEGER = 2_147_483_647


def _is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_comment(comentario, errors):
    if comentario is not None and not isinstance(comentario, str):
        errors.append("comentario debe ser texto o null")


def _validate_rating(calificacion, errors):
    if not _is_integer(calificacion) or not 1 <= calificacion <= 5:
        errors.append("calificacion debe ser un entero entre 1 y 5")


def validate_create_review(data):
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    errors = []
    libro_id = data.get("libro_id")
    if libro_id is None:
        errors.append("libro_id es requerido")
    elif not _is_integer(libro_id) or not 1 <= libro_id <= MAX_INTEGER:
        errors.append("libro_id debe ser un número entero entre 1 y 2147483647")

    calificacion = data.get("calificacion")
    if calificacion is None:
        errors.append("calificacion es requerida")
    else:
        _validate_rating(calificacion, errors)

    _validate_comment(data.get("comentario"), errors)

    if errors:
        raise ValidationError(errors)

    return {
        "libro_id": libro_id,
        "calificacion": calificacion,
        "comentario": data.get("comentario"),
    }


def validate_update_review(data):
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    allowed = {"calificacion", "comentario"}
    if not allowed.intersection(data):
        raise ValidationError(
            ["Debe indicar al menos un campo a actualizar entre calificacion, comentario"]
        )

    errors = []
    if "calificacion" in data:
        _validate_rating(data["calificacion"], errors)
    if "comentario" in data:
        _validate_comment(data["comentario"], errors)

    if errors:
        raise ValidationError(errors)

    result = {}
    if "calificacion" in data:
        result["calificacion"] = data["calificacion"]
    if "comentario" in data:
        result["comentario"] = data["comentario"]
    return result
