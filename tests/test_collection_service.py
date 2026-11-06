import unittest
from unittest.mock import patch

from psycopg2 import IntegrityError
from psycopg2 import errors as pg_errors

from app.errors.exceptions import ConflictError, NotFoundError
from app.services import collection_service
from tests.helpers import make_collection_row


def _patch(name, **kwargs):
    return patch.object(collection_service, name, **kwargs)


class CollectionReadTest(unittest.TestCase):
    def test_list_is_scoped_to_user(self):
        with _patch("fetch_all", return_value=[make_collection_row()]) as fetch_all:
            result = collection_service.list_collections(7)

        self.assertEqual(result[0]["nombre"], "Favoritos")
        self.assertEqual(fetch_all.call_args.args[1], (7,))

    def test_get_includes_owned_books(self):
        with _patch("fetch_one", return_value=make_collection_row()), _patch(
            "fetch_all", return_value=[{"libro_id": 3}]
        ), _patch("get_book", return_value={"id": 3}) as get_book:
            result = collection_service.get_collection(5, 7)

        self.assertEqual(result["libros"], [{"id": 3}])
        get_book.assert_called_once_with(3, 7)

    def test_get_foreign_collection_returns_not_found(self):
        with _patch("fetch_one", return_value=None), self.assertRaises(NotFoundError):
            collection_service.get_collection(5, 99)


class CollectionWriteTest(unittest.TestCase):
    def test_create_returns_the_new_collection(self):
        with _patch("fetch_value", return_value={"id": 5}) as fetch_value, _patch(
            "get_collection", return_value={"id": 5}
        ):
            result = collection_service.create_collection({"nombre": "Favoritos"}, 7)

        self.assertEqual(result, {"id": 5})
        self.assertEqual(fetch_value.call_args.args[1], (7, "Favoritos"))

    def test_create_duplicate_name_is_a_conflict(self):
        with _patch("fetch_value", side_effect=pg_errors.UniqueViolation()), self.assertRaises(
            ConflictError
        ):
            collection_service.create_collection({"nombre": "Favoritos"}, 7)

    def test_create_propagates_other_integrity_errors(self):
        with _patch("fetch_value", side_effect=IntegrityError()), self.assertRaises(IntegrityError):
            collection_service.create_collection({"nombre": "Favoritos"}, 7)

    def test_rename_is_scoped_to_owner(self):
        with _patch("fetch_value", return_value={"id": 5}) as fetch_value, _patch(
            "get_collection", return_value={"id": 5, "nombre": "Leídos"}
        ):
            result = collection_service.rename_collection(5, {"nombre": "Leídos"}, 7)

        self.assertEqual(result["nombre"], "Leídos")
        self.assertEqual(fetch_value.call_args.args[1], ("Leídos", 5, 7))

    def test_rename_foreign_collection_returns_not_found(self):
        with _patch("fetch_value", return_value=None), self.assertRaises(NotFoundError):
            collection_service.rename_collection(5, {"nombre": "Leídos"}, 99)

    def test_rename_duplicate_name_is_a_conflict(self):
        with _patch("fetch_value", side_effect=pg_errors.UniqueViolation()), self.assertRaises(
            ConflictError
        ):
            collection_service.rename_collection(5, {"nombre": "Leídos"}, 7)

    def test_rename_propagates_other_integrity_errors(self):
        with _patch("fetch_value", side_effect=IntegrityError()), self.assertRaises(IntegrityError):
            collection_service.rename_collection(5, {"nombre": "Leídos"}, 7)

    def test_delete_is_scoped_to_owner(self):
        with _patch("fetch_value", return_value={"id": 5}) as fetch_value:
            collection_service.delete_collection(5, 7)

        self.assertEqual(fetch_value.call_args.args[1], (5, 7))

    def test_delete_foreign_collection_returns_not_found(self):
        with _patch("fetch_value", return_value=None), self.assertRaises(NotFoundError):
            collection_service.delete_collection(5, 99)


class CollectionBooksTest(unittest.TestCase):
    def test_add_book_links_it(self):
        with _patch("_get_collection_row"), _patch("fetch_one", return_value={"id": 3}), _patch(
            "fetch_value"
        ) as fetch_value, _patch("get_collection", return_value={"id": 5}):
            result = collection_service.add_book_to_collection(5, 3, 7)

        self.assertEqual(result, {"id": 5})
        self.assertEqual(fetch_value.call_args.args[1], (5, 3))

    def test_add_foreign_book_returns_not_found(self):
        with _patch("_get_collection_row"), _patch("fetch_one", return_value=None), _patch(
            "fetch_value"
        ) as fetch_value:
            with self.assertRaises(NotFoundError):
                collection_service.add_book_to_collection(5, 3, 7)

        fetch_value.assert_not_called()

    def test_remove_book_unlinks_it(self):
        with _patch("_get_collection_row"), _patch(
            "fetch_value", return_value={"libro_id": 3}
        ), _patch("get_collection", return_value={"id": 5, "libros": []}):
            result = collection_service.remove_book_from_collection(5, 3, 7)

        self.assertEqual(result["libros"], [])

    def test_remove_book_not_in_collection_returns_not_found(self):
        with _patch("_get_collection_row"), _patch("fetch_value", return_value=None):
            with self.assertRaises(NotFoundError):
                collection_service.remove_book_from_collection(5, 3, 7)


if __name__ == "__main__":
    unittest.main()
