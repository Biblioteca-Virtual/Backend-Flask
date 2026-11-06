import unittest
from unittest.mock import patch

from app.errors.exceptions import NotFoundError, ValidationError
from app.services import book_service
from tests.helpers import make_book_row, make_review_row

AUTOR = {"id": 2, "nombre": "Jorge Luis", "apellido": "Borges"}


def _patch(name, **kwargs):
    return patch.object(book_service, name, **kwargs)


class BookReadTest(unittest.TestCase):
    def test_list_without_search_sends_null_filter(self):
        with _patch("fetch_all", side_effect=[[make_book_row()], [AUTOR]]) as fetch_all:
            result = book_service.list_books(7)

        self.assertEqual(result[0]["autores"], [AUTOR])
        self.assertEqual(fetch_all.call_args_list[0].args[1], (7, None, None))

    def test_list_with_search_uses_like_parameter(self):
        with _patch("fetch_all", return_value=[]) as fetch_all:
            book_service.list_books(7, search="fic")

        self.assertEqual(fetch_all.call_args.args[1], (7, "%fic%", "%fic%"))

    def test_get_serializes_reading_progress(self):
        with _patch("fetch_one", return_value=make_book_row()), _patch("fetch_all", return_value=[]):
            result = book_service.get_book(3, 7)

        self.assertEqual(result["porcentaje_lectura"], 25)
        self.assertFalse(result["terminado"])
        self.assertEqual(result["categoria"], {"id": 1, "nombre": "General"})

    def test_get_is_scoped_to_owner(self):
        with _patch("fetch_one", return_value=None) as fetch_one:
            with self.assertRaises(NotFoundError):
                book_service.get_book(3, 99)

        self.assertEqual(fetch_one.call_args.args[1], (3, 99))

    def test_book_reviews_include_equivalent_titles(self):
        candidates = [
            {"id": 3, "titulo": "Ficciones"},
            {"id": 8, "titulo": "ficciones!"},
            {"id": 9, "titulo": "El Aleph"},
        ]
        with _patch("get_book", return_value={"titulo": "Ficciones"}), _patch(
            "fetch_all", side_effect=[candidates, [make_review_row()]]
        ) as fetch_all:
            result = book_service.list_book_reviews(3, 7)

        self.assertEqual(fetch_all.call_args.args[1], ([3, 8],))
        self.assertEqual(result[0]["usuario"], "Ada Lovelace")

    def test_book_reviews_always_include_own_book(self):
        with _patch("get_book", return_value={"titulo": "Ficciones"}), _patch(
            "fetch_all", side_effect=[[], []]
        ) as fetch_all:
            book_service.list_book_reviews(3, 7)

        self.assertEqual(fetch_all.call_args.args[1], ([3],))


class BookWriteTest(unittest.TestCase):
    def test_create_defaults_to_general_category_and_links_authors(self):
        data = {"titulo": "Ficciones", "descripcion": None, "autores": [2]}
        with _patch("fetch_all", return_value=[{"id": 2}]), _patch(
            "fetch_value", return_value={"id": 3}
        ) as fetch_value, _patch("execute") as execute, _patch(
            "get_book", return_value={"id": 3}
        ):
            result = book_service.create_book(data, 7)

        self.assertEqual(result, {"id": 3})
        self.assertEqual(fetch_value.call_args.args[1][:4], (7, "Ficciones", None, 1))
        self.assertEqual(execute.call_args.args[1], (3, 2))

    def test_create_rejects_unknown_category(self):
        with _patch("fetch_one", return_value=None), self.assertRaises(ValidationError) as ctx:
            book_service.create_book({"titulo": "X", "descripcion": None, "categoria_id": 40}, 7)

        self.assertEqual(ctx.exception.errors, ["La categoría 40 no existe"])

    def test_create_rejects_unknown_authors(self):
        data = {"titulo": "X", "descripcion": None, "autores": [2, 4]}
        with _patch("fetch_all", return_value=[{"id": 2}]), self.assertRaises(ValidationError) as ctx:
            book_service.create_book(data, 7)

        self.assertEqual(ctx.exception.errors, ["autores no existen: [4]"])

    def test_update_missing_book_returns_not_found(self):
        with _patch("fetch_one", return_value=None), self.assertRaises(NotFoundError):
            book_service.update_book(3, {"titulo": "X"}, 7)

    def test_update_only_touches_sent_fields(self):
        with _patch("_get_libro_row", return_value=make_book_row()), _patch(
            "execute"
        ) as execute, _patch("get_book", return_value={"id": 3}):
            book_service.update_book(3, {"paginas_leidas": 80}, 7)

        params = execute.call_args.args[1]
        self.assertEqual(params[0], None)
        self.assertEqual(params[4], False)
        self.assertEqual(params[6:8], (True, 80))
        self.assertEqual(params[-2:], (3, 7))

    def test_update_validates_new_category(self):
        with _patch("_get_libro_row", return_value=make_book_row()), _patch(
            "fetch_one", return_value={"id": 6}
        ), _patch("execute") as execute, _patch("get_book"):
            book_service.update_book(3, {"categoria_id": 6}, 7)

        self.assertEqual(execute.call_args.args[1][3], 6)

    def test_update_authors_replaces_previous_links(self):
        with _patch("_get_libro_row", return_value=make_book_row()), _patch(
            "fetch_all", return_value=[{"id": 2}]
        ), _patch("execute") as execute, _patch("get_book"):
            book_service.update_book(3, {"autores": [2]}, 7)

        statements = [call.args[0] for call in execute.call_args_list]
        self.assertIn("DELETE FROM libros_autores", statements[0])
        self.assertIn("INSERT INTO libros_autores", statements[1])

    def test_progress_missing_book_returns_not_found(self):
        with _patch("_get_libro_row", return_value=None), self.assertRaises(NotFoundError):
            book_service.update_book_progress(3, {"paginas_leidas": 1}, 7)

    def test_progress_keeps_fields_that_were_not_sent(self):
        with _patch("_get_libro_row", return_value=make_book_row()), _patch(
            "execute"
        ) as execute, _patch("get_book", return_value={"id": 3}):
            book_service.update_book_progress(3, {"paginas_leidas": 80}, 7)

        sql, params = execute.call_args.args
        self.assertIn("usuario_id = %s", sql)
        self.assertEqual(params, (None, 80, 3, 7))

    def test_delete_is_scoped_to_owner(self):
        row = make_book_row()
        with _patch("_get_libro_row", return_value=row), _patch("execute") as execute:
            self.assertEqual(book_service.delete_book(3, 7), row)

        self.assertEqual(execute.call_args.args[1], (3, 7))

    def test_delete_missing_book_returns_not_found(self):
        with _patch("_get_libro_row", return_value=None), self.assertRaises(NotFoundError):
            book_service.delete_book(3, 7)


class CatalogTest(unittest.TestCase):
    def test_list_categories(self):
        with _patch("fetch_all", return_value=[{"id": 1, "nombre": "General"}]):
            self.assertEqual(book_service.list_categories()[0]["nombre"], "General")

    def test_list_authors(self):
        with _patch("fetch_all", return_value=[AUTOR]):
            self.assertEqual(book_service.list_authors(), [AUTOR])

    def test_existing_category_is_not_created_again(self):
        row = {"id": 2, "nombre": "Novela", "descripcion": None}
        with _patch("fetch_one", return_value=row), _patch("fetch_value") as fetch_value:
            result = book_service.create_category({"nombre": "novela"})

        self.assertEqual(result, (row, False))
        fetch_value.assert_not_called()

    def test_new_category_is_created(self):
        row = {"id": 8, "nombre": "Poesía", "descripcion": None}
        with _patch("fetch_one", return_value=None), _patch("fetch_value", return_value=row):
            self.assertEqual(book_service.create_category({"nombre": "Poesía"}), (row, True))

    def test_existing_author_is_not_created_again(self):
        with _patch("fetch_one", return_value=AUTOR), _patch("fetch_value") as fetch_value:
            result = book_service.create_author({"nombre_completo": "jorge luis borges"})

        self.assertEqual(result, (AUTOR, False))
        fetch_value.assert_not_called()

    def test_new_author_splits_first_word_as_name(self):
        with _patch("fetch_one", return_value=None), _patch(
            "fetch_value", return_value=AUTOR
        ) as fetch_value:
            book_service.create_author({"nombre_completo": "Jorge Luis Borges"})

        self.assertEqual(fetch_value.call_args.args[1], ("Jorge", "Luis Borges"))

    def test_lowercase_author_is_capitalized(self):
        with _patch("fetch_one", return_value=None), _patch(
            "fetch_value", return_value=AUTOR
        ) as fetch_value:
            book_service.create_author({"nombre_completo": "julio cortázar"})

        self.assertEqual(fetch_value.call_args.args[1], ("Julio", "Cortázar"))


if __name__ == "__main__":
    unittest.main()
