import io
import unittest
from unittest.mock import MagicMock, patch

from tests.helpers import BaseRouteTestCase


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

    def test_upload_cover_image(self):
        data = {
            "file": (io.BytesIO(b"fake image bytes"), "portada.jpg")
        }
        response = self.client.post(
            "/api/storage/upload",
            data=data,
            content_type="multipart/form-data",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 201)
        res_data = response.get_json()["data"]
        self.assertIn("url", res_data)
        self.assertTrue(res_data["url"].startswith("/api/storage/covers/"))


if __name__ == "__main__":
    unittest.main()
