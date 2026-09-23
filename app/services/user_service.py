from app.db import execute, fetch_one, fetch_value
from app.errors.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.models.user import Usuario
from app.security import create_token, hash_password, is_legacy_password_hash, verify_password


def get_user(user_id):
    row = fetch_one("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    usuario = Usuario.from_row(row)
    if usuario is None:
        raise NotFoundError("Usuario")
    return usuario.to_dict()


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
           RETURNING id, nombre, apellido, email, fecha_registro""",
        (
            data["nombre"],
            data["apellido"],
            data["email"],
            hash_password(data["password"]),
        ),
    )
    return dict(row)


def login(data):
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

    return {
        "token": create_token(usuario.id),
        "usuario": usuario.to_dict(),
    }