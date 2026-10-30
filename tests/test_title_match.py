import unittest

from app.services.title_match import normalize_title, same_book


class TitleMatchTest(unittest.TestCase):
    def test_normalize_removes_accents_case_and_punctuation(self):
        self.assertEqual(
            normalize_title("  Harry Potter y la Cámara de los Secretos!! "),
            "harry potter y la camara de los secretos",
        )

    def test_accent_difference_is_the_same_book(self):
        self.assertTrue(
            same_book(
                "Harry Potter y la camara de los secretos",
                "Harry Potter y la cámara de los secretos",
            )
        )

    def test_small_typos_are_the_same_book(self):
        self.assertTrue(
            same_book(
                "Harry Poter y la camara de los secreto",
                "Harry Potter y la cámara de los secretos",
            )
        )

    def test_books_of_the_same_saga_are_different(self):
        self.assertFalse(
            same_book(
                "Harry Potter y la piedra filosofal",
                "Harry Potter y la cámara de los secretos",
            )
        )

    def test_unrelated_titles_are_different(self):
        self.assertFalse(same_book("El Quijote", "Cien años de soledad"))

    def test_empty_titles_never_match(self):
        self.assertFalse(same_book("", ""))


if __name__ == "__main__":
    unittest.main()
