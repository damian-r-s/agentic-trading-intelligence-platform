import json
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2.extras

from src.core.databases.database import get_conn
from src.core.logging import get_logger

logger = get_logger(__name__)

def get_exchange_info(client) -> dict[str, Any]:
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
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO cache_exchange_info (data, expires_at) VALUES (%s, %s)",
                (json.dumps(data), expires_at)
            )

    return data