# Validación de los datos que llegan a las rutas de colecciones.
from app.errors.exceptions import ValidationError
from app.schemas.common import check_id_field, ensure_dict

# Largo máximo del nombre de una colección (igual que la columna en la base de datos).
MAX_NOMBRE = 100


# Crear o renombrar una colección: el nombre es obligatorio y tiene un largo máximo.
# Devuelve el nombre sin espacios en los extremos.
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


# Agregar un libro a una colección: exige un libro_id válido.
def validate_collection_book(data):
    ensure_dict(data)
    errors = []

    libro_id = data.get("libro_id")
    check_id_field(libro_id, "libro_id", errors, required=True)

    if errors:
        raise ValidationError(errors)

    return {"libro_id": libro_id}
