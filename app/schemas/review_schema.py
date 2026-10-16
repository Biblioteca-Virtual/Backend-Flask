from app.errors.exceptions import ValidationError
from app.schemas.common import (
    check_allowed_fields,
    check_id_field,
    ensure_dict,
    is_integer,
)

REVIEW_UPDATE_FIELDS = {"calificacion", "comentario"}


def _validate_comment(comentario, errors):
    if comentario is not None and not isinstance(comentario, str):
        errors.append("comentario debe ser texto o null")


def _validate_rating(calificacion, errors):
    if not is_integer(calificacion) or not 1 <= calificacion <= 5:
        errors.append("calificacion debe ser un entero entre 1 y 5")


def validate_create_review(data):
    ensure_dict(data)
    errors = []

    libro_id = data.get("libro_id")
    check_id_field(libro_id, "libro_id", errors, required=True)

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
    ensure_dict(data)
    check_allowed_fields(
        data,
        REVIEW_UPDATE_FIELDS,
        "Debe indicar al menos un campo a actualizar entre calificacion, comentario",
    )

    errors = []
    if "calificacion" in data:
        _validate_rating(data["calificacion"], errors)
    if "comentario" in data:
        _validate_comment(data["comentario"], errors)

    if errors:
        raise ValidationError(errors)

    return {k: data[k] for k in REVIEW_UPDATE_FIELDS if k in data}
