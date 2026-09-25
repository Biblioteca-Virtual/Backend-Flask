import unittest
from unittest.mock import patch

from psycopg2 import errors as pg_errors

from app.errors.exceptions import ConflictError, NotFoundError, ValidationError
from app.services import review_service


def _row(**overrides):
    row = {
        "id": 1,
        "libro_id": 3,
        "usuario_id": 7,
        "calificacion": 4,
        "comentario": "Buen libro",
        "fecha_creacion": "2026-09-25T10:00:00",
        "libro_titulo": "Cien años de soledad",
        "usuario_nombre": "Ada",
        "usuario_apellido": "Lovelace",
    }
    row.update(overrides)
    return row


class ReviewServiceTest(unittest.TestCase):
    def test_list_serializes_reviews(self):
        with patch.object(
            review_service,
            "fetch_all",
            return_value=[_row()],
        ) as fetch_all:
            result = review_service.list_reviews()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["usuario"], "Ada Lovelace")
        self.assertIn("ORDER BY r.id", fetch_all.call_args.args[0])

    def test_get_missing_review_returns_not_found(self):
        with patch.object(review_service, "_get_review_row", return_value=None):
            with self.assertRaises(NotFoundError):
                review_service.get_review(1)

    def test_create_uses_authenticated_user(self):
        with (
            patch.object(
                review_service,
                "fetch_one",
                side_effect=[{"id": 3}, {"id": 7}],
            ),
            patch.object(review_service, "fetch_value", return_value={"id": 9}) as fetch_value,
            patch.object(
                review_service,
                "get_review",
                return_value={"id": 9, "usuario_id": 7},
            ),
        ):
            result = review_service.create_review(
                {
                    "libro_id": 3,
                    "calificacion": 5,
                    "comentario": None,
                },
                usuario_id=7,
            )

        self.assertEqual(result["usuario_id"], 7)
        self.assertEqual(fetch_value.call_args.args[1], (3, 7, 5, None))

    def test_create_rejects_missing_book(self):
        with patch.object(review_service, "fetch_one", return_value=None):
            with self.assertRaises(NotFoundError):
                review_service.create_review(
                    {"libro_id": 404, "calificacion": 4, "comentario": None},
                    usuario_id=7,
                )

    def test_create_rejects_duplicate_review(self):
        unique_error = pg_errors.UniqueViolation()
        with (
            patch.object(
                review_service,
                "fetch_one",
                side_effect=[{"id": 3}, {"id": 7}],
            ),
            patch.object(
                review_service,
                "fetch_value",
                side_effect=unique_error,
            ),
            self.assertRaises(ConflictError),
        ):
            review_service.create_review(
                {"libro_id": 3, "calificacion": 4, "comentario": None},
                usuario_id=7,
            )

    def test_update_is_scoped_to_owner(self):
        with (
            patch.object(review_service, "fetch_value", return_value={"id": 1}) as fetch_value,
            patch.object(
                review_service,
                "get_review",
                return_value={"id": 1, "calificacion": 5},
            ),
        ):
            result = review_service.update_review(
                1,
                {"calificacion": 5},
                usuario_id=7,
            )

        self.assertEqual(result["calificacion"], 5)
        sql, params = fetch_value.call_args.args
        self.assertIn("usuario_id = %s", sql)
        self.assertEqual(params, (5, 1, 7))

    def test_update_can_clear_comment(self):
        with (
            patch.object(review_service, "fetch_value", return_value={"id": 1}) as fetch_value,
            patch.object(
                review_service,
                "get_review",
                return_value={"id": 1, "comentario": None},
            ),
        ):
            review_service.update_review(1, {"comentario": None}, usuario_id=7)

        self.assertEqual(fetch_value.call_args.args[1], (None, 1, 7))

    def test_update_missing_or_unowned_review_returns_not_found(self):
        with patch.object(review_service, "fetch_value", return_value=None):
            with self.assertRaises(NotFoundError):
                review_service.update_review(
                    1,
                    {"calificacion": 4},
                    usuario_id=7,
                )

    def test_update_requires_a_field(self):
        with self.assertRaises(ValidationError):
            review_service.update_review(1, {}, usuario_id=7)

    def test_delete_is_scoped_to_owner(self):
        with patch.object(review_service, "fetch_value", return_value={"id": 1}) as fetch_value:
            review_service.delete_review(1, usuario_id=7)

        self.assertEqual(fetch_value.call_args.args[1], (1, 7))

    def test_delete_missing_or_unowned_review_returns_not_found(self):
        with patch.object(review_service, "fetch_value", return_value=None):
            with self.assertRaises(NotFoundError):
                review_service.delete_review(1, usuario_id=7)


if __name__ == "__main__":
    unittest.main()
