import unittest

from app.errors.exceptions import ValidationError
from app.schemas.book_schema import validate_create_book, validate_update_book


class BookSchemaTest(unittest.TestCase):
    def test_create_defaults_to_physical_location(self):
        result = validate_create_book({"titulo": "Ficciones"})

        self.assertEqual(result["ubicacion"], "fisico")
        self.assertIsNone(result["url_lectura"])

    def test_create_ignores_removed_fields(self):
        result = validate_create_book(
            {"titulo": "Ficciones", "isbn": "123", "anio_publicacion": 1944, "cantidad": 2}
        )

        for removed in ("isbn", "anio_publicacion", "cantidad"):
            self.assertNotIn(removed, result)

    def test_web_location_requires_url(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_create_book({"titulo": "Ficciones", "ubicacion": "web"})

        self.assertIn("url_lectura es requerida cuando la ubicación es web", ctx.exception.errors)

    def test_web_location_requires_http_url(self):
        with self.assertRaises(ValidationError):
            validate_create_book(
                {"titulo": "Ficciones", "ubicacion": "web", "url_lectura": "ftp://x"}
            )

    def test_url_is_dropped_when_not_web(self):
        result = validate_create_book(
            {"titulo": "Ficciones", "ubicacion": "kindle", "url_lectura": "https://x.com"}
        )

        self.assertIsNone(result["url_lectura"])

    def test_unknown_location_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_create_book({"titulo": "Ficciones", "ubicacion": "biblioteca"})

    def test_update_url_uses_current_web_location(self):
        result = validate_update_book(
            {"url_lectura": "https://lector.com/libro"}, current_ubicacion="web"
        )

        self.assertEqual(result["ubicacion"], "web")
        self.assertEqual(result["url_lectura"], "https://lector.com/libro")

    def test_update_to_physical_clears_url(self):
        result = validate_update_book(
            {"ubicacion": "fisico"},
            current_ubicacion="web",
            current_url="https://lector.com/libro",
        )

        self.assertIsNone(result["url_lectura"])


if __name__ == "__main__":
    unittest.main()
