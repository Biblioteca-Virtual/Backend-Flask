import unittest
from unittest.mock import patch

from app import create_app
from app.security import create_token


class RouletteRoutesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        with self.app.app_context():
            self.token = create_token(42)
        self.client = self.app.test_client()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_spin_uses_authenticated_user(self):
        reading = {
            "id": 9,
            "usuario_id": 42,
            "libro_id": 3,
            "estado": "activo",
            "progreso": 0,
        }
        with patch(
            "app.routes.roulette.spin",
            return_value=reading,
        ) as service:
            response = self.client.post(
                "/api/roulette/spin",
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 201)
        service.assert_called_once_with(42)
        self.assertEqual(response.get_json()["data"], reading)

    def test_spin_requires_authentication(self):
        response = self.client.post("/api/roulette/spin")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json()["error"],
            "Se requiere token de autenticación",
        )


if __name__ == "__main__":
    unittest.main()
