from app.errors.exceptions import ValidationError
from app.models.book import UBICACIONES
from app.schemas.common import (
    check_allowed_fields,
    check_non_negative_int,
    ensure_dict,
    is_integer,
)

BOOK_FIELDS = {
    "titulo",
    "descripcion",
    "categoria_id",
    "autores",
    "paginas_totales",
    "paginas_leidas",
    "imagen_portada",
    "ubicacion",
    "url_lectura",
}

MAX_URL = 500

_PAGE_FIELDS = ("paginas_totales", "paginas_leidas")


def _valid_autores(autores):
    return isinstance(autores, list) and all(is_integer(a) for a in autores)


def _check_autores_field(autores, errors):
    if autores is not None and not _valid_autores(autores):
        errors.append("autores debe ser una lista de ids")


def _check_paginas(data, errors):
    for field in _PAGE_FIELDS:
        if data.get(field) is not None:
            check_non_negative_int(data.get(field), field, errors)


def _clean_url(value):
    if isinstance(value, str):
        return value.strip() or None
    return value


def _web_url_error(url):
    if not isinstance(url, str) or not url:
        return "url_lectura es requerida cuando la ubicación es web"
    if not url.startswith(("http://", "https://")):
        return "url_lectura debe empezar con http:// o https://"
    if len(url) > MAX_URL:
        return f"url_lectura no puede superar los {MAX_URL} caracteres"
    return None


def _check_ubicacion(ubicacion, url, errors):
    """La URL solo tiene sentido (y es obligatoria) cuando se lee en la web."""
    if ubicacion not in UBICACIONES:
        errors.append("ubicacion debe ser fisico, kindle o web")
        return
    error = _web_url_error(url) if ubicacion == "web" else None
    if error:
        errors.append(error)


def _location_fields(ubicacion, url, errors):
    ubicacion = ubicacion or "fisico"
    _check_ubicacion(ubicacion, url, errors)
    return {"ubicacion": ubicacion, "url_lectura": url if ubicacion == "web" else None}


def _clean_cover(data):
    return (data.get("imagen_portada") or "").strip() or None


def _required_title(data, errors):
    titulo = (data.get("titulo") or "").strip()
    if not titulo:
        errors.append("titulo es requerido")
    return titulo


def _category_or_default(cat_id, errors):
    if cat_id is None or cat_id == "":
        return 1
    if not is_integer(cat_id):
        errors.append("categoria_id debe ser un número entero")
    return cat_id


def _raise_if_errors(errors):
    if errors:
        raise ValidationError(errors)


def validate_create_book(data):
    ensure_dict(data)
    errors = []

    titulo = _required_title(data, errors)
    cat_id = _category_or_default(data.get("categoria_id"), errors)
    _check_autores_field(data.get("autores"), errors)
    _check_paginas(data, errors)
    location = _location_fields(data.get("ubicacion"), _clean_url(data.get("url_lectura")), errors)
    _raise_if_errors(errors)

    return {
        "titulo": titulo,
        "descripcion": data.get("descripcion"),
        "categoria_id": cat_id,
        "autores": data.get("autores") or [],
        "paginas_totales": int(data.get("paginas_totales") or 0),
        "paginas_leidas": int(data.get("paginas_leidas") or 0),
        "imagen_portada": _clean_cover(data),
        **location,
    }


def _check_update_fields(data, errors):
    titulo = data.get("titulo")
    if titulo is not None and not str(titulo).strip():
        errors.append("titulo no puede estar vacío")
    if data.get("categoria_id") is not None and not is_integer(data.get("categoria_id")):
        errors.append("categoria_id debe ser un número entero")
    _check_autores_field(data.get("autores"), errors)
    _check_paginas(data, errors)


def _updated_location(data, current_ubicacion, current_url, errors):
    if "ubicacion" not in data and "url_lectura" not in data:
        return {}
    url = _clean_url(data["url_lectura"]) if "url_lectura" in data else current_url
    return _location_fields(data.get("ubicacion", current_ubicacion), url, errors)


def _updated_fields(data):
    result = {}
    if data.get("titulo") is not None:
        result["titulo"] = str(data["titulo"]).strip()
    if "imagen_portada" in data:
        result["imagen_portada"] = _clean_cover(data)
    for field in ("descripcion", "categoria_id", "autores", "paginas_totales", "paginas_leidas"):
        if field in data:
            result[field] = data[field]
    return result


def validate_update_book(data, current_ubicacion="fisico", current_url=None):
    """Valida una actualización parcial.

    Como la URL depende de la ubicación, se valida contra el estado que quedará
    guardado: lo enviado o, si no se envió, lo actual.
    """
    ensure_dict(data)
    check_allowed_fields(
        data,
        BOOK_FIELDS,
        "Debe indicar al menos un campo a actualizar entre "
        "titulo, descripcion, categoria_id, autores, paginas_totales, "
        "paginas_leidas, imagen_portada, ubicacion, url_lectura",
    )

    errors = []
    _check_update_fields(data, errors)
    location = _updated_location(data, current_ubicacion, current_url, errors)
    _raise_if_errors(errors)
    return {**location, **_updated_fields(data)}


def validate_update_progress(data):
    ensure_dict(data)
    if not any(field in data for field in _PAGE_FIELDS):
        raise ValidationError(["Debe indicar paginas_totales o paginas_leidas"])

    errors = []
    _check_paginas(data, errors)
    _raise_if_errors(errors)
    return {field: int(data[field]) for field in _PAGE_FIELDS if data.get(field) is not None}


def validate_author(data):
    ensure_dict(data)
    completo = data.get("nombre_completo")
    if not isinstance(completo, str) or not completo.strip():
        raise ValidationError(["nombre_completo es requerido"])
    # Un solo espacio entre palabras para que la búsqueda de duplicados funcione.
    completo = " ".join(completo.split())
    if len(completo) > 200:
        raise ValidationError(["nombre_completo no puede superar los 200 caracteres"])
    return {"nombre_completo": completo}


def validate_category(data):
    ensure_dict(data)
    nombre = data.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValidationError(["nombre es requerido"])
    nombre = nombre.strip()
    if len(nombre) > 100:
        raise ValidationError(["nombre no puede superar los 100 caracteres"])
    return {"nombre": nombre}
