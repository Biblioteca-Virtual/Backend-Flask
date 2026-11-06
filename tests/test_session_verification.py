import smtplib
import unittest
from unittest.mock import MagicMock, patch

from app.security import hash_password
from app.services.email_service import send_session_email
from app.services.session_verification_service import _hash
from tests.helpers import BaseRouteTestCase

SERVICE = "app.services.session_verification_service"


def make_user_row(**overrides):
    row = {
        "id": 7,
        "nombre": "Ada",
        "apellido": "Lovelace",
        "email": "ada@example.com",
        "password": hash_password("secreto1"),
        "fecha_registro": "2026-10-30T10:00:00",
        "email_verificado": True,
    }
    row.update(overrides)
    return row


def public_user():
    row = make_user_row()
    row.pop("password")
    return row


class LoginSendsSessionEmailTest(BaseRouteTestCase):
    def test_register_does_not_log_in(self):
        with patch("app.services.user_service.fetch_one", return_value=None), patch(
            "app.services.user_service.fetch_value", return_value=public_user()
        ):
            response = self.client.post(
                "/api/auth/register",
                json={
                    "nombre": "Ada",
                    "apellido": "Lovelace",
                    "email": "ada@example.com",
                    "password": "secreto1",
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertNotIn("token", response.get_json()["data"])

    def test_login_sends_email_and_does_not_return_token(self):
        with patch(
            "app.services.user_service.fetch_one", return_value=make_user_row()
        ), patch(f"{SERVICE}.execute"), patch(f"{SERVICE}.fetch_value") as insert, patch(
            f"{SERVICE}.send_session_email", return_value=True
        ) as send:
            response = self.client.post(
                "/api/auth/login", json={"email": "ada@example.com", "password": "secreto1"}
            )

        self.assertEqual(response.status_code, 202)
        data = response.get_json()["data"]
        self.assertNotIn("token", data)
        self.assertTrue(data["verificacion_pendiente"])
        self.assertTrue(data["correo_enviado"])
        self.assertEqual(data["expira_en_minutos"], 15)

        # Se guardan los hashes, no los secretos.
        token_hash, consulta_hash = insert.call_args.args[1][1:3]
        self.assertEqual(consulta_hash, _hash(data["consulta"]))
        link = send.call_args.args[1]
        self.assertTrue(link.startswith("http://localhost:4200/verificar-sesion?token="))
        self.assertEqual(token_hash, _hash(link.split("token=")[1]))

    def test_wrong_password_sends_nothing(self):
        with patch(
            "app.services.user_service.fetch_one", return_value=make_user_row()
        ), patch(f"{SERVICE}.send_session_email") as send:
            response = self.client.post(
                "/api/auth/login", json={"email": "ada@example.com", "password": "otra"}
            )

        self.assertEqual(response.status_code, 401)
        send.assert_not_called()


class VerifySessionTest(BaseRouteTestCase):
    def test_link_verifies_and_returns_session(self):
        with patch(f"{SERVICE}.fetch_value", return_value={"usuario_id": 7}), patch(
            f"{SERVICE}.execute"
        ) as execute, patch(f"{SERVICE}.fetch_one", return_value=public_user()):
            response = self.client.post("/api/auth/verify-session", json={"token": "abc"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertIn("token", data)
        self.assertEqual(data["usuario"]["email"], "ada@example.com")
        self.assertIn("email_verificado = TRUE", execute.call_args.args[0])

    def test_unknown_link_is_invalid(self):
        with patch(f"{SERVICE}.fetch_value", return_value=None), patch(
            f"{SERVICE}.fetch_one", return_value=None
        ):
            response = self.client.post("/api/auth/verify-session", json={"token": "abc"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["errors"], ["El link de verificación no es válido"])

    def test_expired_link(self):
        with patch(f"{SERVICE}.fetch_value", return_value=None), patch(
            f"{SERVICE}.fetch_one", return_value={"?column?": 1}
        ):
            response = self.client.post("/api/auth/verify-session", json={"token": "abc"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("venció", response.get_json()["errors"][0])

    def test_token_is_required(self):
        response = self.client.post("/api/auth/verify-session", json={})

        self.assertEqual(response.status_code, 400)


class SessionStatusTest(BaseRouteTestCase):
    def status_row(self, **overrides):
        row = {
            "id": 3,
            "usuario_id": 7,
            "verificada_en": None,
            "entregada": False,
            "vencida": False,
        }
        row.update(overrides)
        return row

    def test_pending_until_the_button_is_clicked(self):
        with patch(f"{SERVICE}.fetch_one", return_value=self.status_row()):
            response = self.client.post("/api/auth/session-status", json={"consulta": "q"})

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["data"], {"estado": "pendiente"})

    def test_verified_session_is_delivered_once(self):
        verified = self.status_row(verificada_en="2026-10-30T10:05:00")
        with patch(
            f"{SERVICE}.fetch_one", side_effect=[verified, public_user()]
        ), patch(f"{SERVICE}.fetch_value", return_value={"usuario_id": 7}):
            response = self.client.post("/api/auth/session-status", json={"consulta": "q"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertEqual(data["estado"], "verificada")
        self.assertIn("token", data)

        with patch(f"{SERVICE}.fetch_one", return_value=verified), patch(
            f"{SERVICE}.fetch_value", return_value=None
        ):
            response = self.client.post("/api/auth/session-status", json={"consulta": "q"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("ya se usó", response.get_json()["errors"][0])

    def test_expired_verification(self):
        with patch(f"{SERVICE}.fetch_one", return_value=self.status_row(vencida=True)):
            response = self.client.post("/api/auth/session-status", json={"consulta": "q"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("venció", response.get_json()["errors"][0])

    def test_unknown_consulta(self):
        with patch(f"{SERVICE}.fetch_one", return_value=None):
            response = self.client.post("/api/auth/session-status", json={"consulta": "q"})

        self.assertEqual(response.status_code, 400)

    def test_resend_uses_a_new_link(self):
        row = {"id": 7, "nombre": "Ada", "email": "ada@example.com"}
        with patch(f"{SERVICE}.fetch_value", return_value=row) as update, patch(
            f"{SERVICE}.send_session_email", return_value=True
        ) as send:
            response = self.client.post("/api/auth/resend-session-email", json={"consulta": "q"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["data"]["correo_enviado"])
        new_hash = update.call_args.args[1][0]
        self.assertEqual(new_hash, _hash(send.call_args.args[1].split("token=")[1]))

    def test_resend_after_expiry_fails(self):
        with patch(f"{SERVICE}.fetch_value", return_value=None):
            response = self.client.post("/api/auth/resend-session-email", json={"consulta": "q"})

        self.assertEqual(response.status_code, 400)


class SessionEmailMessageTest(BaseRouteTestCase):
    def setUp(self):
        super().setUp()
        self.usuario = {"id": 7, "nombre": "Ada", "email": "ada@example.com"}
        self.link = "http://localhost:4200/verificar-sesion?token=abc"

    def test_without_mail_config_the_link_is_logged(self):
        self.app.config["MAIL_USERNAME"] = ""
        with self.app.app_context(), patch("smtplib.SMTP") as smtp:
            self.assertFalse(send_session_email(self.usuario, self.link))
        smtp.assert_not_called()

    def test_email_uses_template_link_and_inline_images(self):
        self.app.config.update(MAIL_USERNAME="ambarly@gmail.com", MAIL_PASSWORD="abcd efgh")
        server = MagicMock()
        with self.app.app_context(), patch("smtplib.SMTP") as smtp:
            smtp.return_value.__enter__.return_value = server
            self.assertTrue(send_session_email(self.usuario, self.link))

        server.login.assert_called_once_with("ambarly@gmail.com", "abcdefgh")
        message = server.send_message.call_args.args[0]
        self.assertEqual(message["To"], "ada@example.com")
        self.assertIn("ÁmbarLy", message["From"])
        self.assertEqual(message["Subject"], "Verificá tu sesión en ÁmbarLy")
        html = message.get_body(("html",)).get_content()
        self.assertIn(self.link, html)
        self.assertIn("Verificar Sesión", html)
        self.assertIn("15 minutos", html)
        cids = {
            part["Content-ID"]
            for part in message.walk()
            if part.get_content_maintype() == "image"
        }
        self.assertEqual(cids, {"<logo>", "<bienvenida>"})

    def test_smtp_failure_returns_false(self):
        self.app.config.update(MAIL_USERNAME="ambarly@gmail.com", MAIL_PASSWORD="x")
        with self.app.app_context(), patch(
            "smtplib.SMTP", side_effect=smtplib.SMTPAuthenticationError(535, b"bad")
        ):
            self.assertFalse(send_session_email(self.usuario, self.link))


if __name__ == "__main__":
    unittest.main()
