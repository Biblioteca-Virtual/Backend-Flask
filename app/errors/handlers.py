from flask import current_app, jsonify
from psycopg2 import IntegrityError
from psycopg2 import errors as pg_errors
from werkzeug.exceptions import HTTPException

from app.errors.exceptions import ApiError


def register_error_handlers(app):
    app.register_error_handler(ApiError, handle_api_error)
    app.register_error_handler(IntegrityError, handle_integrity_error)
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_unexpected_error)


def handle_api_error(err):
    return jsonify(err.to_dict()), err.status_code


def handle_integrity_error(err):
    orig = getattr(err, "orig", None)
    if isinstance(err, pg_errors.UniqueViolation) or isinstance(
        orig, pg_errors.UniqueViolation
    ):
        message = "El valor ya existe"
    elif isinstance(err, pg_errors.ForeignKeyViolation) or isinstance(
        orig, pg_errors.ForeignKeyViolation
    ):
        message = "Referencia inválida: el registro relacionado no existe o está en uso"
    else:
        message = "Conflicto con los datos existentes"
    return jsonify({"error": message}), 409


def handle_http_error(err):
    if err.code == 404:
        message = "No se encontró la ruta solicitada"
    elif err.code == 405:
        message = "Método no permitido"
    else:
        message = err.description
    return jsonify({"error": message}), err.code


def handle_unexpected_error(err):
    current_app.logger.exception(err)
    return jsonify({"error": "Error interno del servidor"}), 500