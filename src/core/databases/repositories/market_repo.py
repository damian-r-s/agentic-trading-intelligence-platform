from src.core.databases.database import get_conn

def insert_candles(rows: list[dict]):
    sql = """
        INSERT INTO candles(symbol, interval, open_time, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, interval, open_time) DO NOTHING
    """
    params = [
        (
            r["symbol"],
            r["interval"],
            r["open_time"],
            r["open"],
            r["high"],
            r["low"],
            r["close"],
            r["volume"]
        )
        for r in rows
    ]

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, params)
            return cur.rowcount