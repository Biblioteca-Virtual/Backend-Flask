def format_user_name(nombre, apellido):
    if not nombre:
        return None
    return f"{nombre} {apellido}".strip()
