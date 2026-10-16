from app.errors.exceptions import ValidationError
from app.schemas.common import (
    MAX_INTEGER,
    check_allowed_fields,
    check_id_field,
    ensure_dict,
    is_integer,
)

ESTADOS = {"activo", "devuelto"}
READING_UPDATE_FIELDS = {"progreso", "estado"}


def _is_valid_state(value):
    return isinstance(value, str) and value in ESTADOS


def _validate_progress(progress, errors):
    if not is_integer(progress) or not 0 <= progress <= 100:
        errors.append("progreso debe ser un entero entre 0 y 100")


def validate_create_reading(data):
    ensure_dict(data)
    errors = []

    libro_id = data.get("libro_id")
    check_id_field(libro_id, "libro_id", errors, required=True)

    progress = data.get("progreso", 0)
    _validate_progress(progress, errors)

    if errors:
        raise ValidationError(errors)

    return {"libro_id": libro_id, "progreso": progress}


def validate_update_reading(data):
    ensure_dict(data)
    check_allowed_fields(
        data,
        READING_UPDATE_FIELDS,
        "Debe indicar al menos un campo a actualizar entre progreso, estado",
    )

    errors = []
    if "progreso" in data:
        _validate_progress(data["progreso"], errors)
    if "estado" in data and not _is_valid_state(data["estado"]):
        errors.append(
            "estado debe ser uno de los siguientes valores: "
            f"{', '.join(sorted(ESTADOS))}"
        )

    if errors:
        raise ValidationError(errors)

    return {k: data[k] for k in READING_UPDATE_FIELDS if k in data}


def _parse_filter_libro_id(raw_id, errors):
    if raw_id is None:
        return None
    if isinstance(raw_id, (bool, float)):
        errors.append("libro_id debe ser un número entero entre 1 y 2147483647")
        return None
    try:
        val = int(raw_id)
        if not 1 <= val <= MAX_INTEGER:
            errors.append("libro_id debe ser un número entero entre 1 y 2147483647")
            return None
        return val
    except (TypeError, ValueError):
        errors.append("libro_id debe ser un número entero entre 1 y 2147483647")
        return None


def validate_reading_filters(filters):
    errors = []
    estado = filters.get("estado")
    if estado is not None and not _is_valid_state(estado):
        errors.append(
            "estado debe ser uno de los siguientes valores: "
            f"{', '.join(sorted(ESTADOS))}"
        )

    libro_id = _parse_filter_libro_id(filters.get("libro_id"), errors)

    if errors:
        raise ValidationError(errors)
    return {"estado": estado, "libro_id": libro_id}
