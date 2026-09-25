import unittest

from app.errors.exceptions import ValidationError
from app.schemas.review_schema import (
    validate_create_review,
    validate_update_review,
)


class ReviewSchemaTest(unittest.TestCase):
    def test_create_ignores_client_user_id(self):
        data = validate_create_review(
            {
                "libro_id": 3,
                "usuario_id": 99,
                "calificacion": 4,
                "comentario": "Buen libro",
            }
        )

        self.assertEqual(
            data,
            {
                "libro_id": 3,
                "calificacion": 4,
                "comentario": "Buen libro",
            },
        )

    def test_create_allows_optional_comment(self):
        data = validate_create_review({"libro_id": 3, "calificacion": 5})

        self.assertEqual(data["comentario"], None)

    def test_create_rejects_invalid_values(self):
        invalid_bodies = [
            {"libro_id": 0, "calificacion": 4},
            {"libro_id": True, "calificacion": 4},
            {"libro_id": 2_147_483_648, "calificacion": 4},
            {"libro_id": 3, "calificacion": 0},
            {"libro_id": 3, "calificacion": 6},
            {"libro_id": 3, "calificacion": True},
            {"libro_id": 3, "calificacion": None},
            {"libro_id": 3, "calificacion": "4"},
            {"libro_id": 3, "calificacion": 4, "comentario": []},
        ]

        for body in invalid_bodies:
            with self.subTest(body=body), self.assertRaises(ValidationError):
                validate_create_review(body)

    def test_create_rejects_non_object(self):
        with self.assertRaises(ValidationError):
            validate_create_review(None)

    def test_update_only_returns_provided_fields(self):
        data = validate_update_review(
            {"calificacion": 5, "comentario": None}
        )

        self.assertEqual(data, {"calificacion": 5, "comentario": None})

    def test_update_requires_supported_field(self):
        for body in ({}, {"usuario_id": 2}, {"libro_id": 3}):
            with self.subTest(body=body), self.assertRaises(ValidationError):
                validate_update_review(body)

    def test_update_rejects_invalid_values(self):
        invalid_bodies = [
            {"calificacion": None},
            {"calificacion": 0},
            {"calificacion": 6},
            {"calificacion": False},
            {"comentario": 42},
            {"comentario": []},
        ]

        for body in invalid_bodies:
            with self.subTest(body=body), self.assertRaises(ValidationError):
                validate_update_review(body)


if __name__ == "__main__":
    unittest.main()
