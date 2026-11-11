# Tests de la ruta que cambia el progreso de lectura de un libro.
import unittest
from unittest.mock import patch

from tests.helpers import BaseRouteTestCase


# PATCH /api/books/<id>/progress con el servicio simulado, incluidos los campos null.
class BookProgressAndStorageTest(BaseRouteTestCase):
    def test_patch_book_progress(self):
        updated_book = {
            "id": 1,
            "titulo": "Cien años de soledad",
            "paginas_totales": 500,
            "paginas_leidas": 250,
            "porcentaje_lectura": 50,
        }
        with patch("app.routes.books.update_book_progress", return_value=updated_book) as mock_update:
            response = self.client.patch(
                "/api/books/1/progress",
                json={"paginas_totales": 500, "paginas_leidas": 250},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["porcentaje_lectura"], 50)
        mock_update.assert_called_once_with(1, {"paginas_totales": 500, "paginas_leidas": 250}, 42)

    def test_progress_ignores_null_fields(self):
        with patch("app.routes.books.update_book_progress", return_value={"id": 1}) as mock_update:
            response = self.client.patch(
                "/api/books/1/progress",
                json={"paginas_totales": None, "paginas_leidas": 10},
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        mock_update.assert_called_once_with(1, {"paginas_leidas": 10}, 42)


if __name__ == "__main__":
    unittest.main()
