import unittest

from app.errors.exceptions import ValidationError
from app.schemas.book_schema import (
    validate_author,
    validate_category,
    validate_create_book,
    validate_update_book,
    validate_update_progress,
)


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

    def assert_invalid(self, validator, data, message):
        with self.assertRaises(ValidationError) as ctx:
            validator(data)
        self.assertIn(message, ctx.exception.errors)

    def test_create_requires_title(self):
        self.assert_invalid(validate_create_book, {"titulo": "  "}, "titulo es requerido")

    def test_create_rejects_invalid_fields(self):
        cases = (
            ({"categoria_id": "x"}, "categoria_id debe ser un número entero"),
            ({"autores": "Borges"}, "autores debe ser una lista de ids"),
            ({"paginas_totales": -1}, "paginas_totales debe ser un entero mayor o igual a 0"),
        )
        for field, message in cases:
            with self.subTest(field=field):
                self.assert_invalid(validate_create_book, {"titulo": "X", **field}, message)

    def test_create_rejects_too_long_url(self):
        url = "https://x.com/" + "a" * 500
        self.assert_invalid(
            validate_create_book,
            {"titulo": "X", "ubicacion": "web", "url_lectura": url},
            "url_lectura no puede superar los 500 caracteres",
        )

    def test_create_cleans_blank_cover(self):
        result = validate_create_book({"titulo": "X", "imagen_portada": "  "})

        self.assertIsNone(result["imagen_portada"])
        self.assertEqual(result["categoria_id"], 1)

    def test_update_needs_a_known_field(self):
        with self.assertRaises(ValidationError):
            validate_update_book({"isbn": "123"})

    def test_update_rejects_invalid_fields(self):
        cases = (
            ({"titulo": " "}, "titulo no puede estar vacío"),
            ({"categoria_id": "x"}, "categoria_id debe ser un número entero"),
        )
        for data, message in cases:
            with self.subTest(data=data):
                self.assert_invalid(validate_update_book, data, message)

    def test_update_copies_only_sent_fields(self):
        result = validate_update_book(
            {"titulo": " Nuevo ", "imagen_portada": "", "paginas_leidas": 4}
        )

        self.assertEqual(
            result, {"titulo": "Nuevo", "imagen_portada": None, "paginas_leidas": 4}
        )

    def test_update_null_title_keeps_the_current_one(self):
        self.assertNotIn("titulo", validate_update_book({"titulo": None, "descripcion": "x"}))

    def test_progress_requires_a_field(self):
        self.assert_invalid(
            validate_update_progress, {}, "Debe indicar paginas_totales o paginas_leidas"
        )

    def test_progress_rejects_negative_pages(self):
        self.assert_invalid(
            validate_update_progress,
            {"paginas_leidas": -1},
            "paginas_leidas debe ser un entero mayor o igual a 0",
        )

    def test_author_validation(self):
        self.assertEqual(
            validate_author({"nombre_completo": " J.K.   Rowling "}),
            {"nombre_completo": "J.K. Rowling"},
        )
        self.assert_invalid(validate_author, {}, "nombre_completo es requerido")
        self.assert_invalid(
            validate_author,
            {"nombre_completo": "a" * 201},
            "nombre_completo no puede superar los 200 caracteres",
        )

    def test_category_validation(self):
        self.assertEqual(validate_category({"nombre": " Poesía "}), {"nombre": "Poesía"})
        self.assert_invalid(validate_category, {}, "nombre es requerido")
        self.assert_invalid(
            validate_category,
            {"nombre": "a" * 101},
            "nombre no puede superar los 100 caracteres",
        )

    def test_body_must_be_an_object(self):
        self.assert_invalid(validate_create_book, [], "El cuerpo debe ser un objeto JSON")


if __name__ == "__main__":
    unittest.main()
