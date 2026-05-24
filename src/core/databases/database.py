import os
from contextlib import contextmanager
from typing import Iterator

import psycopg2.extensions
from psycopg2 import pool

from src.core.logging import get_logger

logger = get_logger(__name__)

_pool: pool.ThreadedConnectionPool | None = None

def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        dbname = os.getenv("POSTGRES_DB", "trading")
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=host,
            port=port,
            dbname=dbname,
            user=os.getenv("POSTGRES_USER", "trading"),
            password=os.getenv("POSTGRES_PASSWORD", "trading"),
        )
        logger.info(f"connection pool created host={host} port={port} db={dbname} minconn=1 maxconn=10")
    return _pool


@contextmanager
def get_conn() -> Iterator[psycopg2.extensions.connection]:
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error(f"transaction rolled back: {exc}")
        raise
    finally:
        p.putconn(conn)
