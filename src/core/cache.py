from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2.extras

from src.core.config import get_binance_settings
from src.core.databases.repositories import cache_repo
from src.core.databases.database import get_conn
from src.core.logging import get_logger
from src.exchanges.binance.client import BinanceClient

logger = get_logger(__name__)

class CacheService:

    _EXCHANGE_INFO_TTL = timedelta(hours=24)
    _KLINES_TTL        = timedelta(minutes=15)
    _ORDER_BOOK_TTL    = timedelta(seconds=30)

    def __init__(self, client: BinanceClient):
        self.client = client

    def get_exchange_info(self) -> dict[str, Any]:
        sql = """ 
            SELECT data FROM cache_exchange_info
                    WHERE expires_at > NOW()
                    ORDER BY fetched_at DESC
                    LIMIT 1
        """
        cached = self._fetch_cached(sql=sql)
                
        if cached: 
            logger.debug("exchange_info: cache HIT")
            return cached

        logger.info("exchange_info: cache MISS - fetching from Binance")
        data = self.client.get_exchange_info()

        expires_at = self._expires_at(self._EXCHANGE_INFO_TTL)
        cache_repo.upsert_exchange_info(data, expires_at=expires_at)

        return data

    def get_klines(self, symbol, interval, limit) -> list[Any]:
        sql = """
            SELECT data 
                FROM cache_klines
                    WHERE symbol=%s AND interval=%s AND expires_at > NOW()                             
        """
        cached = self._fetch_cached(sql=sql, params=(symbol, interval))

        if cached and len(cached) >= limit:
            logger.debug("cache_clines: cache HIT")
            return cached[-limit:]
        
        logger.info("cache_clines: cache MISS - fetching from Binance")
        clines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        expires_at = self._expires_at(self._KLINES_TTL)
        cache_repo.upsert_klines(symbol=symbol, interval=interval, data=clines, expires_at=expires_at)

        return clines

    def get_order_book(self, symbol, limit):
        sql = """
            SELECT data 
                FROM cache_order_book
                    WHERE symbol=%s AND expires_at > NOW()
                        ORDER BY fetched_at DESC LIMIT 1
        """

        cached = self._fetch_cached(sql=sql, params=(symbol, ))

        if cached:
            logger.debug("cache_order_book: cache HIT")
            return cached

        logger.info("cache_order_book: cache MISS - fetching from Binance")
        orders = self.client.get_order_book(symbol=symbol, limit=limit)
        expires_at = self._expires_at(self._ORDER_BOOK_TTL)
        cache_repo.insert_order_book(symbol=symbol, data=orders, expires_at=expires_at)        

        return orders
    
    def _expires_at(self, ttl: timedelta) -> datetime:
        return datetime.now(timezone.utc) + ttl
    
    def _fetch_cached(self, sql: str, params: tuple = ()) -> Any | None:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()

        return row["data"] if row else None
    
def create_cache_service() -> CacheService:
    return CacheService(BinanceClient(get_binance_settings()))