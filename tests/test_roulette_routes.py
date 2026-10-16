from unittest.mock import patch

from tests.helpers import BaseRouteTestCase


class RouletteRoutesTest(BaseRouteTestCase):

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
        self.assert_auth_required("/api/roulette/spin", method="post")


if __name__ == "__main__":
    unittest.main()
