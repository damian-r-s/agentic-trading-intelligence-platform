import json
from src.core.databases.database import get_conn

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
        

def insert_trading_decision(run_id, action, confidence, entry_zone, thesis, risks):
    sql = """
        INSERT INTO trading_decisions (run_id, action, confidence, entry_zone, thesis, risks)
        VALUES (%s, %s, %s, %s, %s, %s)
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
                json.dumps(risks) if risks is not None else None
            ))
            return cur.fetchone()[0]
        

    