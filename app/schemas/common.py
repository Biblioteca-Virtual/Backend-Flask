from app.errors.exceptions import ValidationError

MAX_INTEGER = 2_147_483_647


def ensure_dict(data):
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])


def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def check_required_text(data, field, errors):
    val = data.get(field)
    if not val or not str(val).strip():
        errors.append(f"{field} es requerido")
        return None
    return str(val).strip()


def check_positive_int(val, field, errors):
    if val is not None and (not is_integer(val) or val <= 0):
        errors.append(f"{field} debe ser un entero positivo")


def check_non_negative_int(val, field, errors):
    if val is not None and (not is_integer(val) or val < 0):
        errors.append(f"{field} debe ser un entero mayor o igual a 0")


def check_id_field(val, field, errors, required=False):
    if val is None:
        if required:
            errors.append(f"{field} es requerido")
        return
    if not is_integer(val) or not 1 <= val <= MAX_INTEGER:
        errors.append(f"{field} debe ser un número entero entre 1 y {MAX_INTEGER}")


def check_allowed_fields(data, allowed, message):
    if not allowed.intersection(data):
        raise ValidationError([message])
