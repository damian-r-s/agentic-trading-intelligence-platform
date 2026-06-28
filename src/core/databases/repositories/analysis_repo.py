import json
from src.core.databases.database import get_conn

def insert_outcome(decision_id, horizon_hours, price_at_horizon, actual_return, correct):
    sql = """
        INSERT INTO outcomes (decision_id, horizon_hours, price_at_horizon, actual_return, correct)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                decision_id, 
                horizon_hours,
                price_at_horizon,
                actual_return,
                correct)
            )
            return cur.fetchone()[0]


def get_distinct_symbols():
    sql = "SELECT DISTINCT symbol FROM analysis_runs"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in cur.fetchall()]


def get_outcomes_for_metrics(horizon_hours, window_days, symbol=None):
    sql = """
        SELECT td.action, td.confidence, o.actual_return, o.correct
        FROM outcomes o
        JOIN trading_decisions td ON td.id = o.decision_id
        JOIN analysis_runs ar ON ar.id = td.run_id
        WHERE o.horizon_hours = %s
          AND o.evaluated_at >= NOW() - (%s || ' days')::INTERVAL
          AND (%s::TEXT IS NULL OR ar.symbol = %s)
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (horizon_hours, window_days, symbol, symbol))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def insert_signal_metrics(
    symbol,
    horizon_hours,
    window_days,
    total_predictions,
    directional_accuracy,
    information_coefficient,
    simulated_pnl,
    avg_confidence_correct,
    avg_confidence_incorrect,
):
    sql = """
        INSERT INTO signal_metrics (
            symbol, horizon_hours, window_days, total_predictions,
            directional_accuracy, information_coefficient, simulated_pnl,
            avg_confidence_correct, avg_confidence_incorrect
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                symbol,
                horizon_hours,
                window_days,
                total_predictions,
                directional_accuracy,
                information_coefficient,
                simulated_pnl,
                avg_confidence_correct,
                avg_confidence_incorrect,
            ))
            return cur.fetchone()[0]


def get_unevaluated_decisions(horizon_hours):
    sql = """
        SELECT td.id, ar.symbol, td.action, td.price_at_signal, ar.triggered_at
        FROM trading_decisions td
        JOIN analysis_runs ar ON ar.id = td.run_id
        LEFT JOIN outcomes o ON o.decision_id = td.id AND o.horizon_hours = %s
        WHERE o.id IS NULL
          AND ar.triggered_at <= NOW() - (%s || ' hours')::INTERVAL
          AND td.price_at_signal IS NOT NULL
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (horizon_hours, horizon_hours))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

def create_analysis_run(symbol) -> int:
    sql = """
        INSERT INTO analysis_runs (symbol) 
        VALUES (%s) 
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (symbol,))
            return cur.fetchone()[0]
        
def complete_analysis_run(run_id, status):
    sql = """
        UPDATE analysis_runs SET completed_at = NOW(), status = %s
        WHERE id = %s        
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (status, run_id))            
        
def insert_analysis_signal(run_id, node_name, output) -> int:
    sql = """
        INSERT INTO analysis_signals (run_id, node_name, output)
        VALUES (%s, %s, %s)
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (run_id, node_name, json.dumps(output)))
            return cur.fetchone()[0]
        

def insert_trading_decision(run_id, action, confidence, entry_zone, thesis, risks, price_at_signal):
    sql = """
        INSERT INTO trading_decisions (run_id, action, confidence, entry_zone, thesis, risks, price_at_signal)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                run_id, 
                action, 
                confidence, 
                json.dumps(entry_zone) if entry_zone is not None else None, 
                thesis, 
                json.dumps(risks) if risks is not None else None,
                price_at_signal
            ))
            return cur.fetchone()[0]