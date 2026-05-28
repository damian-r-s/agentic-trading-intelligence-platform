import json
from src.core.databases.database import get_conn

def register_model(name, model_type, version, file_path, training_params, eval_metrics):
    sql = """
        INSERT INTO ml_models (
            name, 
            model_type, 
            version, 
            file_path,             
            training_params,
            eval_metrics            
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (name, version) DO UPDATE SET
            file_path       = EXCLUDED.file_path,
            training_params = COALESCE(EXCLUDED.training_params, ml_models.training_params),
            eval_metrics    = COALESCE(EXCLUDED.eval_metrics,    ml_models.eval_metrics),
            trained_at      = NOW()
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                name, model_type, version, file_path,
                json.dumps(training_params) if training_params is not None else None,
                json.dumps(eval_metrics) if eval_metrics is not None else None,
            ))
            return cur.fetchone()[0]


def set_model_active(model_id: int) -> None:
    sql_deactivate = """
        UPDATE ml_models SET is_active = FALSE
        WHERE name = (SELECT name FROM ml_models WHERE id = %s)
    """
    sql_activate = "UPDATE ml_models SET is_active = TRUE WHERE id = %s"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_deactivate, (model_id,))
            cur.execute(sql_activate, (model_id,))
