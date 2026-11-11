# Validaciones reutilizadas por todos los schemas. Cada función agrega sus mensajes a
# la lista `errors` en lugar de cortar, así el cliente recibe todos los errores juntos.
from app.errors.exceptions import ValidationError

# Máximo de un INTEGER de PostgreSQL: un id mayor haría fallar la consulta.
MAX_INTEGER = 2_147_483_647


# El cuerpo del pedido tiene que ser un objeto JSON ({...}); si no, responde 400.
def ensure_dict(data):
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])


# Verdadero solo para enteros reales: en Python True/False también son int, y se excluyen.
def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


# Exige un texto no vacío. Devuelve el texto sin espacios en los extremos, o None si falta.
def check_required_text(data, field, errors):
    val = data.get(field)
    if not val or not str(val).strip():
        errors.append(f"{field} es requerido")
        return None
    return str(val).strip()


# Si el valor viene, tiene que ser un entero mayor o igual a 0 (por ejemplo, páginas).
def check_non_negative_int(val, field, errors):
    if val is not None and (not is_integer(val) or val < 0):
        errors.append(f"{field} debe ser un entero mayor o igual a 0")


# Valida un id: entero entre 1 y MAX_INTEGER. Con required=True además no puede faltar.
def check_id_field(val, field, errors, required=False):
    if val is None:
        if required:
            errors.append(f"{field} es requerido")
        return
    if not is_integer(val) or not 1 <= val <= MAX_INTEGER:
        errors.append(f"{field} debe ser un número entero entre 1 y {MAX_INTEGER}")


# En una actualización parcial, exige que venga al menos uno de los campos permitidos.
def check_allowed_fields(data, allowed, message):
    if not allowed.intersection(data):
        raise ValidationError([message])
