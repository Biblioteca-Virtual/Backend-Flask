import unittest
from unittest.mock import patch

from psycopg2 import IntegrityError
from psycopg2 import errors as pg_errors
from werkzeug.exceptions import BadRequest

from app import create_app


def _raiser(error):
    def view():
        raise error

    return view


class ErrorHandlersTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def response_for(self, error):
        self.app.add_url_rule("/explota", "explota", _raiser(error))
        return self.client.get("/explota")

    def test_unique_violation_is_a_conflict(self):
        response = self.response_for(pg_errors.UniqueViolation())

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"], "El valor ya existe")

    def test_foreign_key_violation_is_a_conflict(self):
        response = self.response_for(pg_errors.ForeignKeyViolation())

        self.assertEqual(response.status_code, 409)
        self.assertIn("Referencia inválida", response.get_json()["error"])

    def test_other_integrity_error_is_a_conflict(self):
        response = self.response_for(IntegrityError())

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"], "Conflicto con los datos existentes")

    def test_unknown_route_returns_json(self):
        response = self.client.get("/no-existe")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "No se encontró la ruta solicitada")

    def test_wrong_method_returns_json(self):
        response = self.client.delete("/health")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.get_json()["error"], "Método no permitido")

    def test_other_http_error_keeps_its_description(self):
        response = self.response_for(BadRequest("Pedido roto"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Pedido roto")

    def test_unexpected_error_hides_the_details(self):
        with patch.object(self.app.logger, "exception") as log:
            response = self.response_for(RuntimeError("clave interna"))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()["error"], "Error interno del servidor")
        log.assert_called_once()


class HealthRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_reports_database_ok(self):
        with patch("app.routes.health.fetch_one"):
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["database"], "ok")

    def test_answers_200_even_with_the_database_down(self):
        with patch("app.routes.health.fetch_one", side_effect=RuntimeError("caída")):
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["database"], "indisponible")


if __name__ == "__main__":
    unittest.main()
