import unittest
from unittest.mock import patch

from app import create_app
from app.security import create_token


class ReadingRoutesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        with self.app.app_context():
            self.token = create_token(42)
        self.client = self.app.test_client()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_uses_authenticated_user_and_filters(self):
        with patch(
            "app.routes.readings.list_readings",
            return_value=[],
        ) as service:
            response = self.client.get(
                "/api/readings?estado=activo&libro_id=3",
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(
            42,
            estado="activo",
            libro_id=3,
        )

    def test_create_ignores_client_user_and_uses_token_user(self):
        with patch(
            "app.routes.readings.create_reading",
            return_value={"id": 1, "usuario_id": 42, "progreso": 25},
        ) as service:
            response = self.client.post(
                "/api/readings/",
                headers=self.headers,
                json={
                    "libro_id": 3,
                    "usuario_id": 99,
                    "progreso": 25,
                },
            )

        self.assertEqual(response.status_code, 201)
        validated, usuario_id = service.call_args.args
        self.assertNotIn("usuario_id", validated)
        self.assertEqual(usuario_id, 42)
        self.assertEqual(response.get_json()["data"]["usuario_id"], 42)

    def test_invalid_progress_returns_400(self):
        response = self.client.post(
            "/api/readings/",
            headers=self.headers,
            json={"libro_id": 3, "progreso": 101},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Datos inválidos")

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            "/api/readings/",
            headers=self.headers,
            data="not-json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Datos inválidos")

    def test_routes_require_authentication(self):
        response = self.client.get("/api/readings/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json()["error"],
            "Se requiere token de autenticación",
        )


if __name__ == "__main__":
    unittest.main()
