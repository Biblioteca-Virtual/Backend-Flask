import unittest
from pathlib import Path

from app import create_app


class OpenApiSpecTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.spec_path = (
            Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"
        )

    def test_spec_is_served_by_the_application(self):
        response = self.client.get("/openapi.yaml")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.mimetype.startswith("application/yaml"))
        self.assertIn("openapi: 3.0.3", response.get_data(as_text=True))
        response.close()

    def test_spec_documents_every_api_endpoint(self):
        spec = self.spec_path.read_text(encoding="utf-8")

        documented_paths = (
            "/health",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/me",
            "/api/books/",
            "/api/books/{book_id}",
            "/api/readings/",
            "/api/readings/{reading_id}",
            "/api/reviews/",
            "/api/reviews/{review_id}",
            "/api/roulette/spin",
            "/openapi.yaml",
        )

        for path in documented_paths:
            with self.subTest(path=path):
                self.assertIn(f"  {path}:", spec)

        self.assertIn("BearerAuth:", spec)
        self.assertIn("application/json:", spec)


if __name__ == "__main__":
    unittest.main()
