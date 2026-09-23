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


class ValidationError(ApiError):
    def __init__(self, errors):
        super().__init__(400, "Datos inválidos", errors)


class NotFoundError(ApiError):
    def __init__(self, resource="Recurso"):
        super().__init__(404, f"{resource} no encontrado")


class UnauthorizedError(ApiError):
    def __init__(self, message="Credenciales inválidas"):
        super().__init__(401, message)


class ConflictError(ApiError):
    def __init__(self, message="Conflicto con los datos existentes"):
        super().__init__(409, message)