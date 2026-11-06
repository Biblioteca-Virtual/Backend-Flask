import os

from dotenv import load_dotenv

# Lee Backend-Flask/.env si existe (credenciales del correo, SECRET_KEY, etc.).
load_dotenv()


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

    STORAGE_DIR = os.getenv(
        "STORAGE_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage")),
    )

    # Link del botón "Verificar Sesión": apunta a la pantalla de Angular que
    # confirma el inicio de sesión contra el backend.
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")
    SESSION_VERIFICATION_MINUTES = int(os.getenv("SESSION_VERIFICATION_MINUTES", "15"))

    # Envío de correos por SMTP (Gmail: smtp.gmail.com, puerto 587 y una
    # "contraseña de aplicación"). Sin MAIL_USERNAME no se envía nada y el link
    # de verificación se escribe en la consola de Flask.
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_SENDER_NAME = os.getenv("MAIL_SENDER_NAME", "ÁmbarLy")
