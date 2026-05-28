import json
from decimal import Decimal
from src.core.databases.database import get_conn

def insert_portfolio_snapshot(balances: dict, total_value_usdt: Decimal) -> int:
    sql = """
        INSERT INTO portfolio_snapshots (balances, total_value_usdt)
        VALUES (%s, %s)
        RETURNING id
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (json.dumps(balances), total_value_usdt))
            return cur.fetchone()[0]