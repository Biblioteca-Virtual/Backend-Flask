# Acceso a PostgreSQL con psycopg2. Usa un pool de conexiones y devuelve las filas
# como diccionarios (RealDictCursor), así el resto del código accede por nombre de columna.
from contextlib import contextmanager

from flask import current_app
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Pool compartido; se crea la primera vez que se pide una conexión.
_pool = None


# Devuelve una conexión del pool. Si el pool todavía no existe, lo crea con los datos
# de la configuración (entre 1 y 10 conexiones abiertas).
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


# Devuelve la conexión al pool para que la reutilice otra consulta.
def close(conn):
    if _pool is not None:
        _pool.putconn(conn)


# Abre una transacción para varias consultas seguidas. Si todo sale bien hace commit;
# si algo falla hace rollback y vuelve a lanzar el error. Uso: `with transaction() as cur:`.
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


# Lectura por defecto de _run_query: cuántas filas afectó la consulta.
def _rowcount(cursor):
    return cursor.rowcount


# Ejecuta una consulta parametrizada y devuelve lo que extraiga `fetch_fn`.
# Con commit=True confirma los cambios (o los deshace si hay error).
# Siempre devuelve la conexión al pool, falle o no.
def _run_query(sql, params=(), fetch_fn=_rowcount, commit=False):
    conn = connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            result = fetch_fn(cursor)
            if commit:
                conn.commit()
            return result
    except Exception:
        if commit:
            conn.rollback()
        raise
    finally:
        close(conn)


# Devuelve todas las filas del resultado (lista de diccionarios).
def fetch_all(sql, params=()):
    return _run_query(sql, params, fetch_fn=lambda c: c.fetchall())


# Devuelve la primera fila o None si no hay resultados.
def fetch_one(sql, params=()):
    return _run_query(sql, params, fetch_fn=lambda c: c.fetchone())


# Para INSERT/UPDATE con RETURNING: devuelve la fila resultante y hace commit.
def fetch_value(sql, params=()):
    return _run_query(sql, params, fetch_fn=lambda c: c.fetchone(), commit=True)


# Para INSERT/UPDATE/DELETE sin resultado: hace commit y devuelve las filas afectadas.
def execute(sql, params=()):
    return _run_query(sql, params, commit=True)
