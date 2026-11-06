import unittest

from app import create_app
from app.security import create_token


class BaseRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        with self.app.app_context():
            self.token = create_token(42)
        self.client = self.app.test_client()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def assert_auth_required(self, path, method="get"):
        fn = getattr(self.client, method.lower())
        response = fn(path)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json()["error"],
            "Se requiere token de autenticación",
        )
        return response


def make_book_row(**overrides):
    row = {
        "id": 3,
        "usuario_id": 7,
        "titulo": "Ficciones",
        "descripcion": None,
        "categoria_id": 1,
        "categoria_nombre": "General",
        "paginas_totales": 200,
        "paginas_leidas": 50,
        "imagen_portada": None,
        "ubicacion": "fisico",
        "url_lectura": None,
    }
    row.update(overrides)
    return row


def make_collection_row(**overrides):
    row = {
        "id": 5,
        "usuario_id": 7,
        "nombre": "Favoritos",
        "fecha_creacion": "2026-10-30T10:00:00",
        "cantidad_libros": 1,
    }
    row.update(overrides)
    return row


def make_review_row(**overrides):
    row = {
        "id": 1,
        "libro_id": 3,
        "usuario_id": 7,
        "calificacion": 4,
        "comentario": "Buen libro",
        "fecha_creacion": "2026-09-25T10:00:00",
        "libro_titulo": "Cien años de soledad",
        "usuario_nombre": "Ada",
        "usuario_apellido": "Lovelace",
    }
    row.update(overrides)
    return row
