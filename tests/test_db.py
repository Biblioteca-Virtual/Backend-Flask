import unittest
from unittest.mock import MagicMock, patch

from app import create_app, db


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


class RunQueryTest(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        connect = patch.object(db, "connect", return_value=self.connection)
        close = patch.object(db, "close")
        connect.start()
        self.close = close.start()
        self.addCleanup(patch.stopall)

    def test_reads_do_not_commit(self):
        self.cursor.fetchall.return_value = [{"id": 1}]

        self.assertEqual(db.fetch_all("SELECT 1"), [{"id": 1}])

        self.connection.commit.assert_not_called()
        self.close.assert_called_once_with(self.connection)

    def test_fetch_one_returns_a_single_row(self):
        self.cursor.fetchone.return_value = {"id": 1}

        self.assertEqual(db.fetch_one("SELECT 1", (1,)), {"id": 1})

        self.cursor.execute.assert_called_once_with("SELECT 1", (1,))

    def test_fetch_value_commits(self):
        self.cursor.fetchone.return_value = {"id": 1}

        self.assertEqual(db.fetch_value("INSERT 1"), {"id": 1})

        self.connection.commit.assert_called_once_with()

    def test_execute_commits_and_returns_rowcount(self):
        self.cursor.rowcount = 3

        self.assertEqual(db.execute("DELETE 1"), 3)

        self.connection.commit.assert_called_once_with()

    def test_failed_write_rolls_back_and_releases_connection(self):
        self.cursor.execute.side_effect = RuntimeError("fallo")

        with self.assertRaises(RuntimeError):
            db.execute("DELETE 1")

        self.connection.rollback.assert_called_once_with()
        self.close.assert_called_once_with(self.connection)

    def test_failed_read_does_not_roll_back(self):
        self.cursor.execute.side_effect = RuntimeError("fallo")

        with self.assertRaises(RuntimeError):
            db.fetch_one("SELECT 1")

        self.connection.rollback.assert_not_called()


class ConnectionPoolTest(unittest.TestCase):
    def setUp(self):
        original = patch.object(db, "_pool", None)
        original.start()
        self.addCleanup(patch.stopall)
        self.app = create_app()

    def test_pool_is_created_once_from_config(self):
        with self.app.app_context(), patch.object(db.pool, "SimpleConnectionPool") as factory:
            first = db.connect()
            second = db.connect()

        factory.assert_called_once()
        self.assertEqual(factory.call_args.kwargs["database"], self.app.config["DB_NAME"])
        self.assertEqual(first, second)

    def test_close_returns_connection_to_the_pool(self):
        connection = MagicMock()
        with self.app.app_context(), patch.object(db.pool, "SimpleConnectionPool") as factory:
            db.connect()
            db.close(connection)

        factory.return_value.putconn.assert_called_once_with(connection)

    def test_close_without_pool_does_nothing(self):
        db.close(MagicMock())


if __name__ == "__main__":
    unittest.main()
