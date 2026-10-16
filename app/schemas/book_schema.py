from app.errors.exceptions import ValidationError
from app.schemas.common import (
    check_allowed_fields,
    check_non_negative_int,
    check_positive_int,
    ensure_dict,
    is_integer,
)

BOOK_FIELDS = {
    "titulo",
    "isbn",
    "descripcion",
    "anio_publicacion",
    "cantidad",
    "categoria_id",
    "autores",
}


def _valid_autores(autores):
    return isinstance(autores, list) and all(
        is_integer(a) for a in autores
    )


def _check_categoria_id(categoria_id, errors, required=False):
    if categoria_id is None:
        if required:
            errors.append("categoria_id es requerido")
    elif not is_integer(categoria_id):
        errors.append("categoria_id debe ser un número entero")


def _check_autores_field(autores, errors, required=False):
    if autores is None and not required:
        return
    if not _valid_autores(autores or []):
        errors.append("autores debe ser una lista de ids")


def _validate_book_common(data, errors, is_create=False):
    check_positive_int(data.get("anio_publicacion"), "anio_publicacion", errors)
    check_categoria_id(data.get("categoria_id"), errors, required=is_create)
    _check_autores_field(data.get("autores"), errors, required=is_create)

    cantidad = data.get("cantidad", 1 if is_create else None)
    if is_create or "cantidad" in data:
        check_non_negative_int(cantidad, "cantidad", errors)


def validate_create_book(data):
    ensure_dict(data)
    errors = []

    titulo = (data.get("titulo") or "").strip()
    if not titulo:
        errors.append("titulo es requerido")

    _validate_book_common(data, errors, is_create=True)
    if errors:
        raise ValidationError(errors)

    return {
        "titulo": titulo,
        "isbn": (data.get("isbn") or "").strip() or None,
        "descripcion": data.get("descripcion"),
        "anio_publicacion": data.get("anio_publicacion"),
        "cantidad": data.get("cantidad", 1),
        "categoria_id": data.get("categoria_id"),
        "autores": data.get("autores", []),
    }


def _collect_update_book_data(data):
    result = {}
    if "titulo" in data:
        result["titulo"] = str(data["titulo"]).strip()
    if "isbn" in data:
        result["isbn"] = (data.get("isbn") or "").strip() or None
    for field in ("descripcion", "anio_publicacion", "cantidad", "categoria_id", "autores"):
        if field in data:
            result[field] = data[field]
    return result


def validate_update_book(data):
    ensure_dict(data)
    check_allowed_fields(
        data,
        BOOK_FIELDS,
        "Debe indicar al menos un campo a actualizar entre "
        "titulo, isbn, descripcion, anio_publicacion, cantidad, "
        "categoria_id, autores",
    )

    errors = []
    _validate_book_common(data, errors, is_create=False)

    titulo = data.get("titulo")
    if titulo is not None and not str(titulo).strip():
        errors.append("titulo no puede estar vacío")

    if errors:
        raise ValidationError(errors)

    return _collect_update_book_data(data)