import unittest
from unittest.mock import patch

from app.errors.exceptions import ConflictError, NotFoundError
from app.services import roulette_service


class RouletteServiceTest(unittest.TestCase):
    def test_selects_only_books_with_available_copies(self):
        with patch.object(
            roulette_service,
            "fetch_one",
            return_value={"id": 3},
        ) as fetch_one:
            result = roulette_service._select_available_book_id()

        self.assertEqual(result, 3)
        sql = fetch_one.call_args.args[0]
        self.assertIn("p.estado = 'activo'", sql)
        self.assertIn("HAVING l.cantidad > COUNT(p.id)", sql)
        self.assertIn("ORDER BY RANDOM()", sql)

    def test_spin_creates_reading_for_authenticated_user(self):
        reading = {
            "id": 9,
            "usuario_id": 7,
            "libro_id": 3,
            "estado": "activo",
            "progreso": 0,
        }
        with (
            patch.object(
                roulette_service,
                "_select_available_book_id",
                return_value=3,
            ),
            patch.object(
                roulette_service,
                "create_reading",
                return_value=reading,
            ) as create_reading,
        ):
            result = roulette_service.spin(usuario_id=7)

        self.assertEqual(result, reading)
        create_reading.assert_called_once_with(
            {"libro_id": 3, "progreso": 0},
            7,
        )

    def test_spin_returns_conflict_when_no_books_are_available(self):
        with (
            patch.object(
                roulette_service,
                "_select_available_book_id",
                return_value=None,
            ),
            patch.object(roulette_service, "create_reading") as create_reading,
            self.assertRaises(ConflictError),
        ):
            roulette_service.spin(usuario_id=7)

        create_reading.assert_not_called()

    def test_spin_retries_when_selected_copy_was_taken(self):
        reading = {"id": 10, "libro_id": 5, "usuario_id": 7}
        with (
            patch.object(
                roulette_service,
                "_select_available_book_id",
                side_effect=[3, 5],
            ),
            patch.object(
                roulette_service,
                "create_reading",
                side_effect=[ConflictError("Sin copias"), reading],
            ) as create_reading,
        ):
            result = roulette_service.spin(usuario_id=7)

        self.assertEqual(result["libro_id"], 5)
        self.assertEqual(create_reading.call_count, 2)
        self.assertEqual(
            create_reading.call_args_list[1].args,
            ({"libro_id": 5, "progreso": 0}, 7),
        )

    def test_spin_retries_when_book_was_removed(self):
        reading = {"id": 11, "libro_id": 5, "usuario_id": 7}
        with (
            patch.object(
                roulette_service,
                "_select_available_book_id",
                side_effect=[3, 5],
            ),
            patch.object(
                roulette_service,
                "create_reading",
                side_effect=[NotFoundError("Libro"), reading],
            ),
        ):
            result = roulette_service.spin(usuario_id=7)

        self.assertEqual(result["id"], 11)

    def test_spin_stops_after_maximum_attempts(self):
        with (
            patch.object(
                roulette_service,
                "_select_available_book_id",
                return_value=3,
            ),
            patch.object(
                roulette_service,
                "create_reading",
                side_effect=ConflictError("Sin copias"),
            ) as create_reading,
            patch.object(roulette_service, "MAX_SPIN_ATTEMPTS", 2),
            self.assertRaises(ConflictError),
        ):
            roulette_service.spin(usuario_id=7)

        self.assertEqual(create_reading.call_count, 2)


if __name__ == "__main__":
    unittest.main()
