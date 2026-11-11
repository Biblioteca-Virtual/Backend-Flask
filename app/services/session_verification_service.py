"""Verificación de cada inicio de sesión con el botón "Verificar Sesión" del correo.

Flujo:
1. `start` (al iniciar sesión con la contraseña correcta): guarda una
   verificación pendiente y manda el correo. Devuelve `consulta`, el secreto
   con el que la pestaña del login pregunta si ya se verificó.
2. `verify` (al tocar el botón del correo): marca la verificación y devuelve
   la sesión, así la pestaña que abrió el link también queda logueada.
3. `check` (la pestaña del login, cada pocos segundos): mientras no se haya
   tocado el botón responde "pendiente"; después entrega la sesión una vez.

De los dos secretos solo se guarda el hash SHA-256.
"""

import hashlib
import secrets

from flask import current_app

from app.db import execute, fetch_one, fetch_value
from app.errors.exceptions import ValidationError
from app.security import create_token
from app.services.email_service import send_session_email

# Mensajes de error que ve el usuario en el frontend.
INVALID_LINK = "El link de verificación no es válido"
EXPIRED = "La verificación venció: iniciá sesión de nuevo"
ALREADY_USED = "Esta verificación ya se usó: iniciá sesión de nuevo"


# Hash SHA-256 del secreto: en la base de datos nunca se guarda el valor original.
def _hash(secret):
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


# Minutos de validez de una verificación (SESSION_VERIFICATION_MINUTES).
def _minutes():
    return current_app.config["SESSION_VERIFICATION_MINUTES"]


# Link del botón del correo: la pantalla del frontend que confirma la sesión.
def _link(token):
    return f"{current_app.config['FRONTEND_URL']}/verificar-sesion?token={token}"


# Arma la sesión que recibe el frontend: el token JWT y los datos del usuario.
def _session(usuario_id):
    row = fetch_one(
        "SELECT id, nombre, apellido, email, email_verificado, fecha_registro FROM usuarios WHERE id = %s",
        (usuario_id,),
    )
    return {"token": create_token(usuario_id), "usuario": dict(row)}


def start(usuario):
    """Crea la verificación pendiente y manda el correo."""
    # Limpia verificaciones viejas del usuario para que la tabla no crezca.
    execute(
        """DELETE FROM verificaciones_sesion
           WHERE usuario_id = %s AND expira_en < CURRENT_TIMESTAMP - INTERVAL '1 day'""",
        (usuario["id"],),
    )
    token = secrets.token_urlsafe(32)
    consulta = secrets.token_urlsafe(32)
    fetch_value(
        """INSERT INTO verificaciones_sesion (usuario_id, token_hash, consulta_hash, expira_en)
           VALUES (%s, %s, %s, CURRENT_TIMESTAMP + make_interval(mins => %s))
           RETURNING id""",
        (usuario["id"], _hash(token), _hash(consulta), _minutes()),
    )
    return {
        "verificacion_pendiente": True,
        "consulta": consulta,
        "email": usuario["email"],
        "correo_enviado": send_session_email(usuario, _link(token)),
        "expira_en_minutos": _minutes(),
    }


def verify(token):
    """Marca la sesión como verificada (botón del correo) y devuelve la sesión."""
    row = fetch_value(
        """UPDATE verificaciones_sesion
           SET verificada_en = COALESCE(verificada_en, CURRENT_TIMESTAMP)
           WHERE token_hash = %s AND expira_en > CURRENT_TIMESTAMP
           RETURNING usuario_id""",
        (_hash(token),),
    )
    if row is None:
        exists = fetch_one(
            "SELECT 1 FROM verificaciones_sesion WHERE token_hash = %s", (_hash(token),)
        )
        raise ValidationError([EXPIRED if exists else INVALID_LINK])

    # Si llegó al correo, el email es suyo.
    execute(
        "UPDATE usuarios SET email_verificado = TRUE WHERE id = %s AND NOT email_verificado",
        (row["usuario_id"],),
    )
    return _session(row["usuario_id"])


def check(consulta):
    """Estado para la pestaña del login: "pendiente" o la sesión ya verificada."""
    row = fetch_one(
        """SELECT id, usuario_id, verificada_en, entregada,
                  expira_en <= CURRENT_TIMESTAMP AS vencida
           FROM verificaciones_sesion WHERE consulta_hash = %s""",
        (_hash(consulta),),
    )
    if row is None:
        raise ValidationError([INVALID_LINK])

    if row["verificada_en"] is not None:
        # La sesión se entrega una sola vez, aunque lleguen dos consultas juntas.
        claimed = fetch_value(
            """UPDATE verificaciones_sesion SET entregada = TRUE
               WHERE id = %s AND NOT entregada RETURNING usuario_id""",
            (row["id"],),
        )
        if claimed is None:
            raise ValidationError([ALREADY_USED])
        return {"estado": "verificada", **_session(claimed["usuario_id"])}

    if row["vencida"]:
        raise ValidationError([EXPIRED])
    return {"estado": "pendiente"}


def resend(consulta):
    """Manda un correo nuevo (con otro link) y renueva el vencimiento."""
    token = secrets.token_urlsafe(32)
    row = fetch_value(
        """UPDATE verificaciones_sesion v
           SET token_hash = %s, expira_en = CURRENT_TIMESTAMP + make_interval(mins => %s)
           FROM usuarios u
           WHERE v.consulta_hash = %s AND u.id = v.usuario_id
             AND v.verificada_en IS NULL AND v.expira_en > CURRENT_TIMESTAMP
           RETURNING u.id, u.nombre, u.email""",
        (_hash(token), _minutes(), _hash(consulta)),
    )
    if row is None:
        raise ValidationError([EXPIRED])
    return {
        "correo_enviado": send_session_email(dict(row), _link(token)),
        "expira_en_minutos": _minutes(),
    }
