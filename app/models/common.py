# Funciones compartidas por los modelos.


# Une nombre y apellido para mostrar al autor de una reseña.
# Si no hay nombre (por ejemplo, el usuario ya no existe) devuelve None.
def format_user_name(nombre, apellido):
    if not nombre:
        return None
    return f"{nombre} {apellido}".strip()
