import numpy as np

from src.core.logging import get_logger
from src.core.databases.repositories.analysis_repo import (
    get_distinct_symbols,
    get_outcomes_for_metrics,
    insert_signal_metrics,
)
from src.core.databases.repositories.users_repo import list_user_ids

logger = get_logger(__name__)

_HORIZONS_HOURS = (4, 24, 72)
_WINDOW_DAYS = (7, 30, 90)


def _compute_metrics(rows: list[dict]) -> dict | None:
    if not rows:
        return None

    # Only BUY/AVOID are directional bets — WAIT has no outcome to score as right or wrong
    directional = [r for r in rows if r["action"] in ("BUY", "AVOID")]
    da = (
        sum(1 for r in directional if r["correct"]) / len(directional)
        if directional else None
    )

    with_confidence = [r for r in rows if r["confidence"] is not None]
    ic = None
    if len(with_confidence) > 1:
        confidences = np.array([float(r["confidence"]) for r in with_confidence])
        returns = np.array([float(r["actual_return"]) for r in with_confidence])
        if confidences.std() > 0 and returns.std() > 0:
            ic = float(np.corrcoef(confidences, returns)[0, 1])

    pnl = sum(
        float(r["actual_return"]) if r["action"] == "BUY" else -float(r["actual_return"])
        for r in directional
    )

    correct_conf = [float(r["confidence"]) for r in directional if r["correct"] and r["confidence"] is not None]
    incorrect_conf = [float(r["confidence"]) for r in directional if not r["correct"] and r["confidence"] is not None]

    return {
        "total_predictions": len(rows),
        "directional_accuracy": da,
        "information_coefficient": ic,
        "simulated_pnl": pnl,
        "avg_confidence_correct": sum(correct_conf) / len(correct_conf) if correct_conf else None,
        "avg_confidence_incorrect": sum(incorrect_conf) / len(incorrect_conf) if incorrect_conf else None,
    }


def run() -> None:
    for user_id in list_user_ids():
        symbols = get_distinct_symbols(user_id)

        for horizon_hours in _HORIZONS_HOURS:
            for window_days in _WINDOW_DAYS:
                for symbol in [None, *symbols]:
                    rows = get_outcomes_for_metrics(horizon_hours, window_days, user_id, symbol)
                    metrics = _compute_metrics(rows)
                    if metrics is None:
                        continue

                    insert_signal_metrics(
                        symbol=symbol, horizon_hours=horizon_hours, window_days=window_days,
                        user_id=user_id, **metrics,
                    )

                    logger.info(
                        f"user_id={user_id} symbol={symbol or 'ALL'} horizon={horizon_hours}h window={window_days}d "
                        f"n={metrics['total_predictions']} DA={metrics['directional_accuracy']} "
                        f"IC={metrics['information_coefficient']} PnL={metrics['simulated_pnl']}"
                    )


if __name__ == "__main__":
    run()
