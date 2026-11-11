# Errores propios de la API. Los servicios los lanzan y handlers.py los convierte en
# una respuesta JSON con el código HTTP que corresponde.


# Error base: guarda el código HTTP, un mensaje general y una lista opcional de errores
# puntuales (por ejemplo, uno por cada campo inválido). to_dict() arma el cuerpo JSON.
class ApiError(Exception):
    def __init__(self, status_code=400, message="Ocurrió un error", errors=None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.errors = errors or []

    def to_dict(self):
        return {
            "error": self.message,
            "errors": self.errors,
        }


# 400: los datos enviados no pasaron la validación; `errors` lista cada problema.
class ValidationError(ApiError):
    def __init__(self, errors):
        super().__init__(400, "Datos inválidos", errors)


# 404: no existe el recurso pedido (o no pertenece al usuario).
class NotFoundError(ApiError):
    def __init__(self, resource="Recurso"):
        super().__init__(404, f"{resource} no encontrado")


# 401: falta el token, es inválido o las credenciales son incorrectas.
class UnauthorizedError(ApiError):
    def __init__(self, message="Credenciales inválidas"):
        super().__init__(401, message)


# 409: el pedido choca con datos que ya existen (por ejemplo, un email repetido).
class ConflictError(ApiError):
    def __init__(self, message="Conflicto con los datos existentes"):
        super().__init__(409, message)
