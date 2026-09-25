import unittest

from app.errors.exceptions import ValidationError
from app.schemas.reading_schema import (
    validate_create_reading,
    validate_reading_filters,
    validate_update_reading,
)


class ReadingSchemaTest(unittest.TestCase):
    def test_create_uses_safe_defaults(self):
        data = validate_create_reading({"libro_id": 3})

        self.assertEqual(data, {"libro_id": 3, "progreso": 0})

    def test_create_accepts_progress(self):
        data = validate_create_reading({"libro_id": 3, "progreso": 50})

        self.assertEqual(data, {"libro_id": 3, "progreso": 50})

    def test_create_rejects_invalid_values(self):
        invalid_bodies = [
            {"libro_id": 0},
            {"libro_id": True},
            {"libro_id": 2_147_483_648},
            {"libro_id": 1, "progreso": -1},
            {"libro_id": 1, "progreso": 101},
            {"libro_id": 1, "progreso": 50.5},
            {"libro_id": 1, "progreso": "50"},
            {"libro_id": 1, "progreso": None},
            {"libro_id": 1, "progreso": []},
        ]

        for body in invalid_bodies:
            with self.subTest(body=body), self.assertRaises(ValidationError):
                validate_create_reading(body)

    def test_update_only_returns_provided_fields(self):
        data = validate_update_reading({"progreso": 80, "estado": "activo"})

        self.assertEqual(data, {"progreso": 80, "estado": "activo"})

    def test_update_rejects_invalid_progress_and_state(self):
        for body in (
            {"progreso": -1},
            {"progreso": 101},
            {"progreso": None},
            {"estado": "terminado"},
            {"estado": []},
            {"estado": {}},
            {"estado": None},
        ):
            with self.subTest(body=body), self.assertRaises(ValidationError):
                validate_update_reading(body)

    def test_update_requires_supported_field(self):
        with self.assertRaises(ValidationError):
            validate_update_reading({"usuario_id": 2})

    def test_filters_are_normalized(self):
        filters = validate_reading_filters({"estado": "activo", "libro_id": "4"})

        self.assertEqual(filters, {"estado": "activo", "libro_id": 4})

    def test_filters_reject_invalid_values(self):
        for filters in (
            {"estado": "otro"},
            {"estado": []},
            {"libro_id": "abc"},
            {"libro_id": 4.5},
            {"libro_id": "-1"},
            {"libro_id": "2147483648"},
        ):
            with self.subTest(filters=filters), self.assertRaises(ValidationError):
                validate_reading_filters(filters)


if __name__ == "__main__":
    unittest.main()
