from app.errors.exceptions import ValidationError


def _require_int(data, field):
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError([f"{field} debe ser un número entero"])
    return value


def _valid_autores(autores):
    return (
        isinstance(autores, list)
        and all(
            isinstance(a, int) and not isinstance(a, bool) for a in autores
        )
    )


def validate_create_book(data):
    errors = []
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    titulo = (data.get("titulo") or "").strip()
    if not titulo:
        errors.append("titulo es requerido")

    anio = data.get("anio_publicacion")
    if anio is not None and (
        isinstance(anio, bool) or not isinstance(anio, int) or anio <= 0
    ):
        errors.append("anio_publicacion debe ser un entero positivo")

    cantidad = data.get("cantidad", 1)
    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 0:
        errors.append("cantidad debe ser un entero mayor o igual a 0")

    categoria_id = data.get("categoria_id")
    if categoria_id is None:
        errors.append("categoria_id es requerido")
    elif isinstance(categoria_id, bool) or not isinstance(categoria_id, int):
        errors.append("categoria_id debe ser un número entero")

    autores = data.get("autores", [])
    if not _valid_autores(autores):
        errors.append("autores debe ser una lista de ids")

    if errors:
        raise ValidationError(errors)

    isbn = (data.get("isbn") or "").strip() or None
    descripcion = data.get("descripcion")

    return {
        "titulo": titulo,
        "isbn": isbn,
        "descripcion": descripcion,
        "anio_publicacion": anio,
        "cantidad": cantidad,
        "categoria_id": categoria_id,
        "autores": autores,
    }


def validate_update_book(data):
    errors = []
    if not isinstance(data, dict):
        raise ValidationError(["El cuerpo debe ser un objeto JSON"])

    allowed = {
        "titulo",
        "isbn",
        "descripcion",
        "anio_publicacion",
        "cantidad",
        "categoria_id",
        "autores",
    }
    provided = {key for key in data if key in allowed}
    if not provided:
        raise ValidationError(
            ["Debe indicar al menos un campo a actualizar entre "
             "titulo, isbn, descripcion, anio_publicacion, cantidad, "
             "categoria_id, autores"]
        )

    anio = data.get("anio_publicacion")
    if anio is not None and (
        isinstance(anio, bool) or not isinstance(anio, int) or anio <= 0
    ):
        errors.append("anio_publicacion debe ser un entero positivo")

    cantidad = data.get("cantidad")
    if cantidad is not None and (
        isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 0
    ):
        errors.append("cantidad debe ser un entero mayor o igual a 0")

    categoria_id = data.get("categoria_id")
    if categoria_id is not None and (
        isinstance(categoria_id, bool) or not isinstance(categoria_id, int)
    ):
        errors.append("categoria_id debe ser un número entero")

    autores = data.get("autores")
    if autores is not None and not _valid_autores(autores):
        errors.append("autores debe ser una lista de ids")

    titulo = data.get("titulo")
    if titulo is not None and not str(titulo).strip():
        errors.append("titulo no puede estar vacío")

    if errors:
        raise ValidationError(errors)

    result = {}
    if titulo is not None:
        result["titulo"] = str(titulo).strip()
    if "isbn" in data:
        result["isbn"] = (data.get("isbn") or "").strip() or None
    if "descripcion" in data:
        result["descripcion"] = data.get("descripcion")
    if "anio_publicacion" in data:
        result["anio_publicacion"] = anio
    if "cantidad" in data:
        result["cantidad"] = cantidad
    if "categoria_id" in data:
        result["categoria_id"] = categoria_id
    if "autores" in data:
        result["autores"] = autores
    return result