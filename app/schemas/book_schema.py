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


def _valid_autores(autores):
    return isinstance(autores, list) and all(is_integer(a) for a in autores)


def _check_autores_field(autores, errors):
    if autores is not None and not _valid_autores(autores):
        errors.append("autores debe ser una lista de ids")


def _check_paginas(data, errors):
    for field in ("paginas_totales", "paginas_leidas"):
        if data.get(field) is not None:
            check_non_negative_int(data.get(field), field, errors)


def _clean_url(value):
    if isinstance(value, str):
        return value.strip() or None
    return value


def _check_ubicacion(ubicacion, url, errors):
    """La URL solo tiene sentido (y es obligatoria) cuando se lee en la web."""
    if ubicacion not in UBICACIONES:
        errors.append("ubicacion debe ser fisico, kindle o web")
        return
    if ubicacion != "web":
        return
    if not isinstance(url, str) or not url:
        errors.append("url_lectura es requerida cuando la ubicación es web")
    elif not url.startswith(("http://", "https://")):
        errors.append("url_lectura debe empezar con http:// o https://")
    elif len(url) > MAX_URL:
        errors.append(f"url_lectura no puede superar los {MAX_URL} caracteres")


def validate_create_book(data):
    ensure_dict(data)
    errors = []

    titulo = (data.get("titulo") or "").strip()
    if not titulo:
        errors.append("titulo es requerido")

    cat_id = data.get("categoria_id")
    if cat_id is None or cat_id == "":
        cat_id = 1
    elif not is_integer(cat_id):
        errors.append("categoria_id debe ser un número entero")

    _check_autores_field(data.get("autores"), errors)
    _check_paginas(data, errors)

    ubicacion = data.get("ubicacion") or "fisico"
    url = _clean_url(data.get("url_lectura"))
    _check_ubicacion(ubicacion, url, errors)

    if errors:
        raise ValidationError(errors)

    return {
        "titulo": titulo,
        "descripcion": data.get("descripcion"),
        "categoria_id": cat_id,
        "autores": data.get("autores") or [],
        "paginas_totales": int(data.get("paginas_totales") or 0),
        "paginas_leidas": int(data.get("paginas_leidas") or 0),
        "imagen_portada": (data.get("imagen_portada") or "").strip() or None,
        "ubicacion": ubicacion,
        "url_lectura": url if ubicacion == "web" else None,
    }


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
    titulo = data.get("titulo")
    if titulo is not None and not str(titulo).strip():
        errors.append("titulo no puede estar vacío")
    if data.get("categoria_id") is not None and not is_integer(data.get("categoria_id")):
        errors.append("categoria_id debe ser un número entero")
    _check_autores_field(data.get("autores"), errors)
    _check_paginas(data, errors)

    result = {}
    if "ubicacion" in data or "url_lectura" in data:
        ubicacion = data.get("ubicacion", current_ubicacion) or "fisico"
        url = _clean_url(data["url_lectura"]) if "url_lectura" in data else current_url
        _check_ubicacion(ubicacion, url, errors)
        result["ubicacion"] = ubicacion
        result["url_lectura"] = url if ubicacion == "web" else None

    if errors:
        raise ValidationError(errors)

    if "titulo" in data:
        result["titulo"] = str(data["titulo"]).strip()
    if "imagen_portada" in data:
        result["imagen_portada"] = (data.get("imagen_portada") or "").strip() or None
    for field in ("descripcion", "categoria_id", "autores", "paginas_totales", "paginas_leidas"):
        if field in data:
            result[field] = data[field]
    return result


def validate_update_progress(data):
    ensure_dict(data)
    errors = []

    if "paginas_totales" not in data and "paginas_leidas" not in data:
        raise ValidationError(["Debe indicar paginas_totales o paginas_leidas"])

    _check_paginas(data, errors)
    if errors:
        raise ValidationError(errors)

    result = {}
    if "paginas_totales" in data:
        result["paginas_totales"] = int(data["paginas_totales"])
    if "paginas_leidas" in data:
        result["paginas_leidas"] = int(data["paginas_leidas"])
    return result


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
