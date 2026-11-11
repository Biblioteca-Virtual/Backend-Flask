# Configuración de la aplicación. Todo se lee de variables de entorno (archivo .env),
# con valores por defecto pensados para el desarrollo local.
import os

from dotenv import load_dotenv

# Lee Backend-Flask/.env si existe (credenciales del correo, SECRET_KEY, etc.).
load_dotenv()


# Convierte la lista separada por comas de CORS_ORIGINS en una lista de orígenes,
# sin espacios y sin entradas vacías.
def _cors_origins():
    raw = os.getenv("CORS_ORIGINS", "http://localhost:4200")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# Seguridad: clave para firmar los tokens JWT, horas que dura un token y minutos que
# tiene el usuario para confirmar un inicio de sesión desde el correo.
class SecurityConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "cambiar-en-produccion-clave-de-32-caracteres-minimo")
    TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "24"))
    SESSION_VERIFICATION_MINUTES = int(os.getenv("SESSION_VERIFICATION_MINUTES", "15"))


# CORS_ORIGINS lleva los orígenes permitidos separados por coma: el frontend Angular
# corre en http://localhost:4200 durante el desarrollo. FRONTEND_URL es el destino del
# botón "Verificar Sesión": la pantalla de Angular que confirma el inicio de sesión.
# STORAGE_DIR es la carpeta donde se guardan las portadas subidas (por defecto, storage/).
class WebConfig:
    CORS_ORIGINS = _cors_origins()
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")
    STORAGE_DIR = os.getenv(
        "STORAGE_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage")),
    )


# Datos de conexión a PostgreSQL.
class DatabaseConfig:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "biblioteca_db")
    DB_USER = os.getenv("DB_USER", "biblioteca_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "biblioteca_password")


# Envío de correos por SMTP (Gmail: smtp.gmail.com, puerto 587 y una "contraseña de
# aplicación"). Sin MAIL_USERNAME no se envía nada y el link de verificación se escribe
# en la consola de Flask.
class MailConfig:
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_SENDER_NAME = os.getenv("MAIL_SENDER_NAME", "ÁmbarLy")


# Junta las cuatro partes en una sola clase, que es la que carga create_app().
# Están separadas para que cada una tenga una sola responsabilidad.
class Config(SecurityConfig, WebConfig, DatabaseConfig, MailConfig):
    pass
