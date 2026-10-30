import unittest
from unittest.mock import patch

from app.errors.exceptions import ConflictError
from app.services import roulette_service


class RouletteServiceTest(unittest.TestCase):
    def test_spin_returns_random_book(self):
        book = {
            "id": 3,
            "titulo": "Cien años de soledad",
            "paginas_totales": 471,
            "paginas_leidas": 150,
            "porcentaje_lectura": 32,
        }
        with (
            patch.object(roulette_service, "fetch_one", return_value={"id": 3}),
            patch.object(roulette_service, "get_book", return_value=book) as mock_get,
        ):
            result = roulette_service.spin(7)

        self.assertEqual(result, book)
        mock_get.assert_called_once_with(3, 7)

    def test_spin_raises_conflict_when_no_books(self):
        with (
            patch.object(roulette_service, "fetch_one", return_value=None),
            self.assertRaises(ConflictError),
        ):
            roulette_service.spin(7)


if __name__ == "__main__":
    unittest.main()
