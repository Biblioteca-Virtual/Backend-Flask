import unittest
from unittest.mock import patch

from app import create_app
from app.security import create_token


class ReviewRoutesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        with self.app.app_context():
            self.token = create_token(42)
        self.client = self.app.test_client()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_reviews(self):
        with patch(
            "app.routes.reviews.list_reviews",
            return_value=[{"id": 1}],
        ) as service:
            response = self.client.get("/api/reviews", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with()
        self.assertEqual(response.get_json()["data"], [{"id": 1}])

    def test_get_review(self):
        with patch(
            "app.routes.reviews.get_review",
            return_value={"id": 1, "calificacion": 4},
        ) as service:
            response = self.client.get("/api/reviews/1", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(1)

    def test_create_uses_authenticated_user_and_ignores_client_user(self):
        with patch(
            "app.routes.reviews.create_review",
            return_value={"id": 1, "usuario_id": 42},
        ) as service:
            response = self.client.post(
                "/api/reviews",
                headers=self.headers,
                json={
                    "libro_id": 3,
                    "usuario_id": 99,
                    "calificacion": 4,
                    "comentario": "Excelente",
                },
            )

        self.assertEqual(response.status_code, 201)
        validated, usuario_id = service.call_args.args
        self.assertNotIn("usuario_id", validated)
        self.assertEqual(usuario_id, 42)

    def test_update_uses_authenticated_user(self):
        with patch(
            "app.routes.reviews.update_review",
            return_value={"id": 1, "calificacion": 5},
        ) as service:
            response = self.client.put(
                "/api/reviews/1",
                headers=self.headers,
                json={"calificacion": 5},
            )

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(1, {"calificacion": 5}, 42)

    def test_delete_uses_authenticated_user(self):
        with patch("app.routes.reviews.delete_review") as service:
            response = self.client.delete("/api/reviews/1", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(1, 42)

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            "/api/reviews",
            headers=self.headers,
            data="not-json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Datos inválidos")

    def test_routes_require_authentication(self):
        for method, path in (
            ("get", "/api/reviews"),
            ("get", "/api/reviews/1"),
            ("post", "/api/reviews"),
            ("put", "/api/reviews/1"),
            ("delete", "/api/reviews/1"),
        ):
            with self.subTest(method=method, path=path):
                response = getattr(self.client, method)(path)

                self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
