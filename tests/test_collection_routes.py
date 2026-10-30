import unittest
from unittest.mock import patch

from tests.helpers import BaseRouteTestCase


class CollectionRoutesTest(BaseRouteTestCase):

    def test_list_collections_of_authenticated_user(self):
        with patch(
            "app.routes.collections.list_collections",
            return_value=[{"id": 1, "nombre": "Favoritos"}],
        ) as service:
            response = self.client.get("/api/collections", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(42)
        self.assertEqual(response.get_json()["data"][0]["nombre"], "Favoritos")

    def test_create_collection_trims_name(self):
        with patch(
            "app.routes.collections.create_collection",
            return_value={"id": 1, "nombre": "Favoritos"},
        ) as service:
            response = self.client.post(
                "/api/collections",
                headers=self.headers,
                json={"nombre": "  Favoritos  "},
            )

        self.assertEqual(response.status_code, 201)
        service.assert_called_once_with({"nombre": "Favoritos"}, 42)

    def test_create_collection_requires_name(self):
        response = self.client.post(
            "/api/collections", headers=self.headers, json={"nombre": "   "}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("nombre es requerido", response.get_json()["errors"])

    def test_rename_collection_with_put_and_patch(self):
        for method in ("put", "patch"):
            with self.subTest(method=method), patch(
                "app.routes.collections.rename_collection",
                return_value={"id": 1, "nombre": "Leídos"},
            ) as service:
                response = getattr(self.client, method)(
                    "/api/collections/1",
                    headers=self.headers,
                    json={"nombre": "Leídos"},
                )

            self.assertEqual(response.status_code, 200)
            service.assert_called_once_with(1, {"nombre": "Leídos"}, 42)

    def test_add_book_to_collection(self):
        with patch(
            "app.routes.collections.add_book_to_collection",
            return_value={"id": 1, "libros": [{"id": 3}]},
        ) as service:
            response = self.client.post(
                "/api/collections/1/books",
                headers=self.headers,
                json={"libro_id": 3},
            )

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(1, 3, 42)

    def test_add_book_requires_valid_id(self):
        response = self.client.post(
            "/api/collections/1/books",
            headers=self.headers,
            json={"libro_id": "tres"},
        )

        self.assertEqual(response.status_code, 400)

    def test_remove_book_from_collection(self):
        with patch(
            "app.routes.collections.remove_book_from_collection",
            return_value={"id": 1, "libros": []},
        ) as service:
            response = self.client.delete(
                "/api/collections/1/books/3", headers=self.headers
            )

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(1, 3, 42)

    def test_delete_collection(self):
        with patch("app.routes.collections.delete_collection") as service:
            response = self.client.delete("/api/collections/1", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(1, 42)

    def test_routes_require_authentication(self):
        for method, path in (
            ("get", "/api/collections"),
            ("get", "/api/collections/1"),
            ("post", "/api/collections"),
            ("put", "/api/collections/1"),
            ("delete", "/api/collections/1"),
            ("post", "/api/collections/1/books"),
            ("delete", "/api/collections/1/books/3"),
        ):
            with self.subTest(method=method, path=path):
                self.assert_auth_required(path, method=method)


if __name__ == "__main__":
    unittest.main()
