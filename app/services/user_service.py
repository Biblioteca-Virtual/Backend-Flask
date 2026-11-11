# Lógica de negocio de usuarios: consulta, registro e inicio de sesión.
from app.db import execute, fetch_one, fetch_value
from app.errors.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.models.user import Usuario
from app.security import hash_password, is_legacy_password_hash, verify_password
from app.services import session_verification_service


# Datos de un usuario (sin la contraseña); 404 si no existe.
def get_user(user_id):
    row = fetch_one("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    usuario = Usuario.from_row(row)
    if usuario is None:
        raise NotFoundError("Usuario")
    return usuario.to_dict()


# Registra un usuario nuevo. Rechaza emails repetidos con 409 y guarda la contraseña
# hasheada con Argon2. Devuelve los datos públicos del usuario creado.
def register(data):
    existing = fetch_one(
        "SELECT id FROM usuarios WHERE email = %s",
        (data["email"],),
    )
    if existing:
        raise ConflictError("Ya existe un usuario con ese email")

    row = fetch_value(
        """INSERT INTO usuarios (nombre, apellido, email, password)
           VALUES (%s, %s, %s, %s)
           RETURNING id, nombre, apellido, email, email_verificado, fecha_registro""",
        (
            data["nombre"],
            data["apellido"],
            data["email"],
            hash_password(data["password"]),
        ),
    )
    return dict(row)


def login(data):
    """Valida la contraseña y manda el correo de "Verificar Sesión".

    No devuelve el token: la sesión se entrega cuando se toca el botón del
    correo (ver `session_verification_service`).
    """
    row = fetch_one("SELECT * FROM usuarios WHERE email = %s", (data["email"],))
    usuario = Usuario.from_row(row)
    if usuario is None or not verify_password(
        usuario.password, data["password"]
    ):
        raise UnauthorizedError("Email o contraseña incorrectos")

    if is_legacy_password_hash(usuario.password):
        execute(
            "UPDATE usuarios SET password = %s WHERE id = %s",
            (hash_password(data["password"]), usuario.id),
        )

    return session_verification_service.start(usuario.to_dict())
