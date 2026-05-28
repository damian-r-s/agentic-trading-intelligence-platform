import json
from src.core.databases.database import get_conn

def upsert_exchange_info(data, expires_at) -> int:
    sql = """
        INSERT INTO cache_exchange_info(data, expires_at)
        VALUES (%s, %s)
        RETURNING id
    """
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(data), expires_at))
            return cur.fetchone()[0]

def upsert_klines(symbol, interval, data, expires_at):
    sql = """
        INSERT INTO cache_klines(symbol, interval, data, expires_at)        
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (symbol, interval) DO UPDATE SET
            data = EXCLUDED.data,
            fetched_at = NOW(),
            expires_at = EXCLUDED.expires_at
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (symbol, interval, json.dumps(data), expires_at))
            return cur.fetchone()[0]

def insert_order_book(symbol, data, expires_at) -> int:
    sql = """
        INSERT INTO cache_order_book (symbol, data, expires_at)
        VALUES (%s, %s, %s)
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (symbol, json.dumps(data), expires_at))
            return cur.fetchone()[0]