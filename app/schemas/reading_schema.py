from app.errors.exceptions import ValidationError

ESTADOS = {"activo", "devuelto"}
MAX_INTEGER = 2_147_483_647


def _is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_valid_state(value):
    return isinstance(value, str) and value in ESTADOS


def _validate_progress(progress, errors):
    if not _is_integer(progress) or not 0 <= progress <= 100:
        errors.append("progreso debe ser un entero entre 0 y 100")


def validate_create_reading(data):
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    errors = []
    libro_id = data.get("libro_id")
    if not _is_integer(libro_id) or libro_id <= 0 or libro_id > MAX_INTEGER:
        errors.append("libro_id debe ser un número entero entre 1 y 2147483647")

    progress = data.get("progreso", 0)
    _validate_progress(progress, errors)

    if errors:
        raise ValidationError(errors)

    return {"libro_id": libro_id, "progreso": progress}


def validate_update_reading(data):
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    allowed = {"progreso", "estado"}
    provided = allowed.intersection(data)
    if not provided:
        raise ValidationError(
            ["Debe indicar al menos un campo a actualizar entre progreso, estado"]
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

    result = {}
    if "progreso" in data:
        result["progreso"] = data["progreso"]
    if "estado" in data:
        result["estado"] = data["estado"]
    return result


def validate_reading_filters(filters):
    errors = []
    estado = filters.get("estado")
    if estado is not None and not _is_valid_state(estado):
        errors.append(
            "estado debe ser uno de los siguientes valores: "
            f"{', '.join(sorted(ESTADOS))}"
        )

    libro_id = None
    raw_libro_id = filters.get("libro_id")
    if raw_libro_id is not None:
        if isinstance(raw_libro_id, (bool, float)):
            errors.append("libro_id debe ser un número entero entre 1 y 2147483647")
        else:
            try:
                libro_id = int(raw_libro_id)
            except (TypeError, ValueError):
                errors.append("libro_id debe ser un número entero entre 1 y 2147483647")
            else:
                if not 1 <= libro_id <= MAX_INTEGER:
                    errors.append(
                        "libro_id debe ser un número entero entre 1 y 2147483647"
                    )

    if errors:
        raise ValidationError(errors)
    return {"estado": estado, "libro_id": libro_id}
