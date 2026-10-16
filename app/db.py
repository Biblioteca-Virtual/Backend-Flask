from contextlib import contextmanager

from flask import current_app
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

_pool = None


def connect():
    global _pool
    if _pool is None:
        cfg = current_app.config
        _pool = pool.SimpleConnectionPool(
            1,
            10,
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            database=cfg["DB_NAME"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
        )
    return _pool.getconn()


def close(conn):
    if _pool is not None:
        _pool.putconn(conn)


@contextmanager
def transaction():
    conn = connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        close(conn)


def _run_query(sql, params=(), fetch_fn=None, commit=False):
    conn = connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            result = fetch_fn(cursor) if fetch_fn else cursor.rowcount
            if commit:
                conn.commit()
            return result
    except Exception:
        if commit:
            conn.rollback()
        raise
    finally:
        close(conn)


def fetch_all(sql, params=()):
    return _run_query(sql, params, fetch_fn=lambda c: c.fetchall())


def fetch_one(sql, params=()):
    return _run_query(sql, params, fetch_fn=lambda c: c.fetchone())


def fetch_value(sql, params=()):
    return _run_query(sql, params, fetch_fn=lambda c: c.fetchone(), commit=True)


def execute(sql, params=()):
    return _run_query(sql, params, commit=True)
