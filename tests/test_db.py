import unittest
from unittest.mock import MagicMock, patch

from app import db


class DatabaseTransactionTest(unittest.TestCase):
    def test_transaction_commits_and_returns_connection(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        with (
            patch.object(db, "connect", return_value=connection),
            patch.object(db, "close") as close,
            db.transaction(),
        ):
            cursor.execute("SELECT 1")

        connection.commit.assert_called_once_with()
        connection.rollback.assert_not_called()
        close.assert_called_once_with(connection)

    def test_transaction_rolls_back_on_error(self):
        connection = MagicMock()
        with (
            patch.object(db, "connect", return_value=connection),
            patch.object(db, "close") as close,
            self.assertRaises(RuntimeError),
            db.transaction(),
        ):
            raise RuntimeError("fallo")

        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()
        close.assert_called_once_with(connection)


if __name__ == "__main__":
    unittest.main()
