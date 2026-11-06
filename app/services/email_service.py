import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from flask import current_app, render_template

_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "email", "images")

# Imágenes del correo, adjuntas "inline": el HTML las referencia como cid:<nombre>.
_INLINE_IMAGES = ("logo", "bienvenida")


def send_session_email(usuario, link):
    """Manda el correo de "Verificar Sesión" de un inicio de sesión.

    Si el correo no está configurado (sin MAIL_USERNAME) no se envía nada y el
    link se escribe en la consola, para poder probar en desarrollo.

    Returns:
        True si el correo se envió.
    """
    config = current_app.config
    context = {
        "link": link,
        "nombre": usuario["nombre"],
        "minutos": config["SESSION_VERIFICATION_MINUTES"],
    }

    if not config["MAIL_USERNAME"]:
        current_app.logger.warning(
            "Correo sin configurar: link para verificar la sesión de %s -> %s",
            usuario["email"],
            link,
        )
        return False

    return _send(_build_message(usuario["email"], context))


def _send(message):
    config = current_app.config
    try:
        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=15) as smtp:
            smtp.starttls()
            smtp.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"].replace(" ", ""))
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError):
        # La pantalla de espera ofrece reenviarlo.
        current_app.logger.exception("No se pudo enviar el correo de verificación")
        return False
    return True


def _build_message(destinatario, context):
    config = current_app.config
    message = EmailMessage()
    message["Subject"] = "Verificá tu sesión en ÁmbarLy"
    message["From"] = formataddr((config["MAIL_SENDER_NAME"], config["MAIL_USERNAME"]))
    message["To"] = destinatario
    message.set_content(render_template("email/verificacion.txt", **context))
    message.add_alternative(render_template("email/verificacion.html", **context), subtype="html")

    html_part = message.get_payload()[1]
    for name in _INLINE_IMAGES:
        with open(os.path.join(_IMAGES_DIR, f"{name}.png"), "rb") as image:
            html_part.add_related(
                image.read(), maintype="image", subtype="png", cid=f"<{name}>", filename=f"{name}.png"
            )
    return message
