import os


def _cors_origins():
    raw = os.getenv("CORS_ORIGINS", "http://localhost:4200")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cambiar-en-produccion-clave-de-32-caracteres-minimo")
    TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "24"))

    # Origenes permitidos por CORS, separados por coma. El frontend Angular corre
    # en http://localhost:4200 durante el desarrollo.
    CORS_ORIGINS = _cors_origins()

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "biblioteca_db")
    DB_USER = os.getenv("DB_USER", "biblioteca_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "biblioteca_password")