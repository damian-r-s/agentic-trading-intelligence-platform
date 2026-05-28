import json
from src.core.databases.database import get_conn

def create_backtest_run(strategy_name, symbol, start_date, end_date, params=None) -> int:
    sql = """
        INSERT INTO backtest_runs (strategy_name, symbol, start_date, end_date, params)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                strategy_name, symbol, start_date, end_date,
                json.dumps(params) if params is not None else None,
            ))
            return cur.fetchone()[0]

def insert_backtest_trades(run_id, trades: list[dict]) -> int:
    sql = """
        INSERT INTO backtest_trades (run_id, symbol, side, price, quantity, traded_at, pnl)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = [
        (run_id, t["symbol"], t["side"], t["price"],
         t["quantity"], t["traded_at"], t.get("pnl"))
        for t in trades
    ]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, params)
            return cur.rowcount

def insert_backtest_results(run_id, metrics: dict) -> int:
    sql = """
        INSERT INTO backtest_results
            (run_id, total_return, sharpe_ratio, max_drawdown,
             hit_rate, avg_holding_hours, total_trades)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                run_id,
                metrics.get("total_return"),
                metrics.get("sharpe_ratio"),
                metrics.get("max_drawdown"),
                metrics.get("hit_rate"),
                metrics.get("avg_holding_hours"),
                metrics.get("total_trades"),
            ))
            return cur.fetchone()[0]