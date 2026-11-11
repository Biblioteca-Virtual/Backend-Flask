# Manejadores globales de errores: toda excepción termina como una respuesta JSON
# con la forma {"error": "..."} y el código HTTP adecuado.
from flask import current_app, jsonify
from psycopg2 import IntegrityError
from psycopg2 import errors as pg_errors
from werkzeug.exceptions import HTTPException

from app.errors.exceptions import ApiError


# Registra un manejador por tipo de error. Flask usa el más específico, así que
# Exception solo atrapa lo que no encaja en los anteriores.
def register_error_handlers(app):
    app.register_error_handler(ApiError, handle_api_error)
    app.register_error_handler(IntegrityError, handle_integrity_error)
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_unexpected_error)


# Errores propios (ValidationError, NotFoundError, etc.): usa su mensaje y su código.
def handle_api_error(err):
    return jsonify(err.to_dict()), err.status_code


# Restricciones de la base de datos: valor único repetido o clave foránea inválida.
# Siempre responde 409, con un mensaje distinto según el caso.
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


# Errores HTTP de Flask/Werkzeug (ruta inexistente, método no permitido, etc.),
# con los mensajes más comunes traducidos al español.
def handle_http_error(err):
    if err.code == 404:
        message = "No se encontró la ruta solicitada"
    elif err.code == 405:
        message = "Método no permitido"
    else:
        message = err.description
    return jsonify({"error": message}), err.code


# Cualquier otro error: lo registra en el log con el detalle completo y al cliente le
# responde un 500 genérico, sin exponer información interna.
def handle_unexpected_error(err):
    current_app.logger.exception(err)
    return jsonify({"error": "Error interno del servidor"}), 500
