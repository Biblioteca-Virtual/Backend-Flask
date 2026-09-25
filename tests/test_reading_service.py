import unittest
from unittest.mock import MagicMock, patch

from app.errors.exceptions import ConflictError, NotFoundError, ValidationError
from app.services import reading_service


def _row(**overrides):
    row = {
        "id": 1,
        "usuario_id": 7,
        "libro_id": 3,
        "fecha_prestamo": "2026-09-25T10:00:00",
        "fecha_devolucion": None,
        "fecha_actualizacion": "2026-09-25T10:00:00",
        "estado": "activo",
        "progreso": 40,
        "libro_cantidad": 2,
        "libro_titulo": "Cien años de soledad",
        "usuario_nombre": "Ada",
        "usuario_apellido": "Lovelace",
    }
    row.update(overrides)
    return row


def _transaction(cursor):
    context = MagicMock()
    context.__enter__.return_value = cursor
    context.__exit__.return_value = False
    return context


class ReadingServiceTest(unittest.TestCase):
    def test_create_locks_book_and_serializes_progress(self):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [
            {"id": 3, "cantidad": 2},
            {"total": 0},
            {"id": 9},
        ]
        created = _row(id=9, progreso=25)
        with (
            patch.object(
                reading_service,
                "transaction",
                return_value=_transaction(cursor),
            ),
            patch.object(
                reading_service,
                "_get_reading_row",
                return_value=created,
            ),
        ):
            result = reading_service.create_reading(
                {"libro_id": 3, "progreso": 25},
                usuario_id=7,
            )

        self.assertEqual(result["progreso"], 25)
        self.assertEqual(result["usuario"], "Ada Lovelace")
        self.assertEqual(cursor.execute.call_count, 3)
        self.assertEqual(
            cursor.execute.call_args_list[2].args[1],
            (7, 3, 25),
        )

    def test_create_rejects_when_copies_are_unavailable(self):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [
            {"id": 3, "cantidad": 1},
            {"total": 1},
        ]
        with (
            patch.object(
                reading_service,
                "transaction",
                return_value=_transaction(cursor),
            ),
            self.assertRaises(ConflictError),
        ):
            reading_service.create_reading(
                {"libro_id": 3, "progreso": 0},
                usuario_id=7,
            )

        self.assertEqual(cursor.execute.call_count, 2)

    def test_update_progress_preserves_active_state(self):
        cursor = MagicMock()
        current = _row()
        updated = _row(progreso=75)
        with (
            patch.object(
                reading_service,
                "transaction",
                return_value=_transaction(cursor),
            ),
            patch.object(
                reading_service,
                "_get_reading_row_for_update",
                return_value=current,
            ),
            patch.object(
                reading_service,
                "_get_reading_row",
                return_value=updated,
            ),
        ):
            result = reading_service.update_reading(
                1,
                {"progreso": 75},
                usuario_id=7,
            )

        self.assertEqual(result["progreso"], 75)
        self.assertEqual(
            cursor.execute.call_args.args[1],
            (75, "activo", 1, 7),
        )

    def test_update_to_returned_preserves_progress_and_sets_date(self):
        cursor = MagicMock()
        current = _row(progreso=100)
        returned = _row(
            estado="devuelto",
            fecha_devolucion="2026-09-26T10:00:00",
            progreso=100,
        )
        with (
            patch.object(
                reading_service,
                "transaction",
                return_value=_transaction(cursor),
            ),
            patch.object(
                reading_service,
                "_get_reading_row_for_update",
                return_value=current,
            ),
            patch.object(
                reading_service,
                "_get_reading_row",
                return_value=returned,
            ),
        ):
            result = reading_service.update_reading(
                1,
                {"estado": "devuelto"},
                usuario_id=7,
            )

        self.assertEqual(result["estado"], "devuelto")
        self.assertEqual(result["progreso"], 100)
        self.assertIn("COALESCE", cursor.execute.call_args.args[0])
        self.assertEqual(
            cursor.execute.call_args.args[1],
            (100, "devuelto", 1, 7),
        )

    def test_update_reactivating_returned_reading_checks_availability(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {"total": 1}
        current = _row(
            estado="devuelto",
            fecha_devolucion="2026-09-26T10:00:00",
            libro_cantidad=1,
        )
        with (
            patch.object(
                reading_service,
                "transaction",
                return_value=_transaction(cursor),
            ),
            patch.object(
                reading_service,
                "_get_reading_row_for_update",
                return_value=current,
            ),
            self.assertRaises(ConflictError),
        ):
            reading_service.update_reading(
                1,
                {"estado": "activo"},
                usuario_id=7,
            )

        self.assertEqual(cursor.execute.call_count, 1)
        self.assertEqual(cursor.execute.call_args.args[1], (3, 1))

    def test_update_rejects_invalid_progress(self):
        cursor = MagicMock()
        with (
            patch.object(
                reading_service,
                "transaction",
                return_value=_transaction(cursor),
            ),
            patch.object(
                reading_service,
                "_get_reading_row_for_update",
                return_value=_row(),
            ),
            self.assertRaises(ValidationError),
        ):
            reading_service.update_reading(
                1,
                {"progreso": 101},
                usuario_id=7,
            )

    def test_reading_lookup_is_scoped_to_owner(self):
        with (
            patch.object(
                reading_service,
                "fetch_one",
                return_value=None,
            ) as fetch_one,
            self.assertRaises(NotFoundError),
        ):
            reading_service.get_reading(1, usuario_id=7)

        self.assertEqual(fetch_one.call_args.args[1], (1, 7))

    def test_list_applies_owner_and_optional_filters(self):
        with patch.object(
            reading_service,
            "fetch_all",
            return_value=[_row()],
        ) as fetch_all:
            result = reading_service.list_readings(
                usuario_id=7,
                estado="activo",
                libro_id=3,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            fetch_all.call_args.args[1],
            (7, "activo", "activo", 3, 3),
        )

    def test_delete_is_scoped_to_owner(self):
        with patch.object(
            reading_service,
            "fetch_value",
            return_value={"id": 1},
        ) as fetch_value:
            reading_service.delete_reading(1, usuario_id=7)

        self.assertEqual(fetch_value.call_args.args[1], (1, 7))

    def test_delete_missing_reading_returns_not_found(self):
        with (
            patch.object(reading_service, "fetch_value", return_value=None),
            self.assertRaises(NotFoundError),
        ):
            reading_service.delete_reading(1, usuario_id=7)


if __name__ == "__main__":
    unittest.main()
