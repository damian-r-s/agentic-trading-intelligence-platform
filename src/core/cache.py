from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2.extras

from src.core.databases.repositories import cache_repo
from src.core.databases.database import get_conn
from src.core.logging import get_logger
from src.exchanges.binance.client import BinanceClient

logger = get_logger(__name__)

def get_exchange_info(client: BinanceClient) -> dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(""" 
                SELECT data FROM cache_exchange_info
                        WHERE expires_at > NOW()
                        ORDER BY fetched_at DESC
                        LIMIT 1
            """)
            row = cur.fetchone()

    
    if row: 
        logger.debug("exchange_info: cache HIT")
        return row["data"] # already a dic - psycopg2 parses JSONB automatically

    logger.info("exchange_info: cache MISS - fetching from Binance")
    data = client.get_exchange_info()

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    cache_repo.upsert_exchange_info(data, expires_at=expires_at)

    return data

def get_klines(client: BinanceClient, symbol, interval, limit) -> list[Any]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, symbol, interval, data, fetched_at, expires_at 
                    FROM cache_klines
                        WHERE symbol=%s AND interval=%s AND expires_at > NOW()                             
            """, (symbol, interval)) # Binance orders cliens automatically
            cached = cur.fetchone()

    if cached and len(cached["data"]) >= limit:
        logger.debug("cache_clines: cache HIT")
        return cached["data"][-limit:]
    
    logger.info("cache_clines: cache MISS - fetching from Binance")
    clines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    cache_repo.upsert_klines(symbol=symbol, interval=interval, data=clines, expires_at=expires_at)

    return clines

def get_order_book(client, symbol, limit):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, symbol, data, fetched_at, expires_at 
                    FROM cache_order_book
                        WHERE symbol=%s AND expires_at > NOW()
                            ORDER BY fetched_at DESC LIMIT 1
            """, (symbol, ))
            cached = cur.fetchone()

    if cached:
        logger.debug("cache_order_book: cache HIT")
        return cached["data"]

    logger.info("cache_order_book: cache MISS - fetching from Binance")
    orders = client.get_order_book(symbol=symbol, limit=limit)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    cache_repo.insert_order_book(symbol=symbol, data=orders, expires_at=expires_at)        

    return orders