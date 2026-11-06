import unittest
from unittest.mock import patch

from tests.helpers import BaseRouteTestCase


class BookRoutesTest(BaseRouteTestCase):
    def test_list_is_scoped_to_authenticated_user(self):
        with patch("app.routes.books.list_books", return_value=[]) as service:
            response = self.client.get("/api/books/", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(42, search=None)

    def test_create_is_owned_by_authenticated_user(self):
        with patch("app.routes.books.create_book", return_value={"id": 1}) as service:
            response = self.client.post(
                "/api/books/", headers=self.headers, json={"titulo": "Ficciones"}
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(service.call_args.args[1], 42)

    def test_book_reviews_include_similar_titles(self):
        with patch(
            "app.routes.books.list_book_reviews", return_value=[{"id": 9}]
        ) as service:
            response = self.client.get("/api/books/3/reviews", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(3, 42)

    def test_new_category_returns_201(self):
        with patch(
            "app.routes.books.create_category",
            return_value=({"id": 8, "nombre": "Poesía"}, True),
        ) as service:
            response = self.client.post(
                "/api/books/categories", headers=self.headers, json={"nombre": " Poesía "}
            )

        self.assertEqual(response.status_code, 201)
        service.assert_called_once_with({"nombre": "Poesía"})

    def test_existing_category_returns_200(self):
        with patch(
            "app.routes.books.create_category",
            return_value=({"id": 2, "nombre": "Novela"}, False),
        ):
            response = self.client.post(
                "/api/books/categories", headers=self.headers, json={"nombre": "novela"}
            )

        self.assertEqual(response.status_code, 200)

    def test_new_author_normalizes_spaces_and_returns_201(self):
        with patch(
            "app.routes.books.create_author",
            return_value=({"id": 6, "nombre": "J.K.", "apellido": "Rowling"}, True),
        ) as service:
            response = self.client.post(
                "/api/books/authors",
                headers=self.headers,
                json={"nombre_completo": "  J.K.   Rowling "},
            )

        self.assertEqual(response.status_code, 201)
        service.assert_called_once_with({"nombre_completo": "J.K. Rowling"})

    def test_existing_author_returns_200(self):
        with patch(
            "app.routes.books.create_author",
            return_value=({"id": 2, "nombre": "Jorge Luis", "apellido": "Borges"}, False),
        ):
            response = self.client.post(
                "/api/books/authors",
                headers=self.headers,
                json={"nombre_completo": "jorge luis borges"},
            )

        self.assertEqual(response.status_code, 200)

    def test_author_requires_name(self):
        response = self.client.post(
            "/api/books/authors", headers=self.headers, json={"nombre_completo": " "}
        )

        self.assertEqual(response.status_code, 400)

    def test_catalog_lists(self):
        for path, service in (
            ("/api/books/categories", "list_categories"),
            ("/api/books/authors", "list_authors"),
        ):
            with self.subTest(path=path), patch(f"app.routes.books.{service}", return_value=[]):
                self.assertEqual(self.client.get(path, headers=self.headers).status_code, 200)

    def test_get_book_is_scoped_to_user(self):
        with patch("app.routes.books.get_book", return_value={"id": 3}) as service:
            response = self.client.get("/api/books/3", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(3, 42)

    def test_put_validates_against_current_location(self):
        current = {"id": 3, "ubicacion": "web", "url_lectura": "https://lector.com/libro"}
        with patch("app.routes.books.get_book", return_value=current), patch(
            "app.routes.books.update_book", return_value={"id": 3}
        ) as service:
            response = self.client.put(
                "/api/books/3", headers=self.headers, json={"ubicacion": "kindle"}
            )

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(3, {"ubicacion": "kindle", "url_lectura": None}, 42)

    def test_delete_book(self):
        with patch("app.routes.books.delete_book") as service:
            response = self.client.delete("/api/books/3", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(3, 42)

    def test_routes_require_authentication(self):
        for method, path in (
            ("get", "/api/books/authors"),
            ("post", "/api/books/authors"),
            ("get", "/api/books/"),
            ("post", "/api/books/categories"),
            ("get", "/api/books/1/reviews"),
        ):
            with self.subTest(method=method, path=path):
                self.assert_auth_required(path, method=method)


if __name__ == "__main__":
    unittest.main()
