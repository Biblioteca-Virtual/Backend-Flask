import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from werkzeug.security import generate_password_hash

from app.errors.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from app.schemas.user_schema import validate_login, validate_register
from app.security import hash_password, verify_password
from app.services import user_service
from tests.helpers import BaseRouteTestCase

VALID_USER = {
    "nombre": " Ada ",
    "apellido": "Lovelace",
    "email": "ADA@Example.com",
    "password": "secreto1",
}


class UserSchemaTest(unittest.TestCase):
    def test_register_normalizes_fields(self):
        result = validate_register(VALID_USER)

        self.assertEqual(result["nombre"], "Ada")
        self.assertEqual(result["email"], "ada@example.com")

    def test_register_reports_every_missing_field(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_register({})

        self.assertEqual(
            ctx.exception.errors,
            ["nombre es requerido", "apellido es requerido", "email es requerido", "password es requerido"],
        )

    def test_register_rejects_invalid_email(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_register({**VALID_USER, "email": "sin-arroba"})

        self.assertEqual(ctx.exception.errors, ["email no tiene un formato válido"])

    def test_register_rejects_short_password(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_register({**VALID_USER, "password": "abc"})

        self.assertEqual(ctx.exception.errors, ["password debe tener al menos 6 caracteres"])

    def test_login_requires_both_fields(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_login({})

        self.assertEqual(ctx.exception.errors, ["email es requerido", "password es requerido"])


class UserServiceTest(unittest.TestCase):
    def test_get_user_hides_nothing_it_should_not_return(self):
        row = {
            "id": 7,
            "nombre": "Ada",
            "apellido": "Lovelace",
            "email": "ada@example.com",
            "password": "hash",
            "fecha_registro": "2026-10-30",
        }
        with patch.object(user_service, "fetch_one", return_value=row):
            result = user_service.get_user(7)

        self.assertEqual(result["email"], "ada@example.com")
        self.assertNotIn("password", result)

    def test_get_missing_user_returns_not_found(self):
        with patch.object(user_service, "fetch_one", return_value=None), self.assertRaises(NotFoundError):
            user_service.get_user(7)

    def test_register_rejects_existing_email(self):
        with patch.object(user_service, "fetch_one", return_value={"id": 7}), self.assertRaises(ConflictError):
            user_service.register({"email": "ada@example.com"})

    def test_login_upgrades_legacy_password_hash(self):
        row = {
            "id": 7,
            "nombre": "Ada",
            "apellido": "Lovelace",
            "email": "ada@example.com",
            "password": generate_password_hash("secreto1"),
            "fecha_registro": "2026-10-30",
        }
        with patch.object(user_service, "fetch_one", return_value=row), patch.object(
            user_service, "execute"
        ) as execute, patch.object(user_service.session_verification_service, "start") as start:
            user_service.login({"email": "ada@example.com", "password": "secreto1"})

        new_hash, user_id = execute.call_args.args[1]
        self.assertTrue(new_hash.startswith("$argon2"))
        self.assertEqual(user_id, 7)
        start.assert_called_once()

    def test_login_unknown_email_is_unauthorized(self):
        with patch.object(user_service, "fetch_one", return_value=None), self.assertRaises(UnauthorizedError):
            user_service.login({"email": "x@example.com", "password": "secreto1"})


class PasswordTest(unittest.TestCase):
    def test_argon2_password(self):
        stored = hash_password("secreto1")

        self.assertTrue(verify_password(stored, "secreto1"))
        self.assertFalse(verify_password(stored, "otra"))

    def test_legacy_password(self):
        stored = generate_password_hash("secreto1")

        self.assertTrue(verify_password(stored, "secreto1"))
        self.assertFalse(verify_password(stored, "otra"))


class TokenRouteTest(BaseRouteTestCase):
    def test_me_returns_the_authenticated_user(self):
        with patch("app.routes.auth.get_user", return_value={"id": 42}) as get_user:
            response = self.client.get("/api/auth/me", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        get_user.assert_called_once_with(42)

    def test_expired_token_is_rejected(self):
        payload = {"sub": "42", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
        token = jwt.encode(payload, self.app.config["SECRET_KEY"], algorithm="HS256")

        response = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "El token ha expirado")

    def test_invalid_token_is_rejected(self):
        response = self.client.get("/api/auth/me", headers={"Authorization": "Bearer basura"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "Token inválido")


if __name__ == "__main__":
    unittest.main()
