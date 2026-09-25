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


def fetch_all(sql, params=()):
    conn = connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        close(conn)


def fetch_one(sql, params=()):
    conn = connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        close(conn)


def fetch_value(sql, params=()):
    conn = connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.fetchone()
    finally:
        close(conn)


def execute(sql, params=()):
    conn = connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        close(conn)
