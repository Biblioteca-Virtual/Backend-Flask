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
    is_number = is_integer(calificacion) or isinstance(calificacion, float)
    if not is_number or not 0.5 <= calificacion <= 5 or calificacion * 2 != int(calificacion * 2):
        errors.append("calificacion debe ser un valor entre 0.5 y 5, de a 0.5")


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
