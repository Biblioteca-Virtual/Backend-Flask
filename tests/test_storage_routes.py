import io
import os
import tempfile
import unittest

from tests.helpers import BaseRouteTestCase


class StorageRoutesTest(BaseRouteTestCase):
    def setUp(self):
        super().setUp()
        # Sin esto, cada corrida deja archivos en el storage/ real del proyecto.
        storage = tempfile.TemporaryDirectory()
        self.addCleanup(storage.cleanup)
        self.storage_dir = storage.name
        self.app.config["STORAGE_DIR"] = self.storage_dir

    def upload(self, filename, content=b"fake image bytes"):
        return self.client.post(
            "/api/storage/upload",
            data={"file": (io.BytesIO(content), filename)},
            content_type="multipart/form-data",
            headers=self.headers,
        )

    def test_upload_saves_cover_with_a_unique_name(self):
        response = self.upload("portada.JPG")

        self.assertEqual(response.status_code, 201)
        data = response.get_json()["data"]
        self.assertTrue(data["url"].startswith("/api/storage/covers/"))
        self.assertTrue(data["filename"].endswith(".jpg"))
        saved = os.path.join(self.storage_dir, "covers", data["filename"])
        self.assertTrue(os.path.exists(saved))

    def test_uploaded_cover_can_be_read_back(self):
        url = self.upload("portada.png").get_json()["data"]["url"]

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"fake image bytes")
        response.close()

    def test_upload_requires_the_file_field(self):
        response = self.client.post(
            "/api/storage/upload",
            data={},
            content_type="multipart/form-data",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("campo 'file'", response.get_json()["errors"][0])

    def test_upload_rejects_empty_filename(self):
        response = self.upload("")

        self.assertEqual(response.status_code, 400)

    def test_upload_rejects_disallowed_extension(self):
        response = self.upload("virus.exe")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Tipo de archivo no permitido", response.get_json()["errors"][0])

    def test_upload_requires_authentication(self):
        self.assert_auth_required("/api/storage/upload", method="post")


if __name__ == "__main__":
    unittest.main()
