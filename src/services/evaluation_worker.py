from src.core.config import get_binance_settings
from src.core.logging import get_logger
from src.core.databases.repositories.analysis_repo import (
    get_unevaluated_decisions,
    insert_outcome,
)
from src.exchanges.binance.client import BinanceClient

logger = get_logger(__name__)

_HORIZONS_HOURS = (4, 24, 72)


def _current_price(client: BinanceClient, symbol: str) -> float:
    ticker = client.get_ticker_prices(symbols=[symbol])
    return float(ticker[0]["price"])


def _evaluate_decision(client: BinanceClient, decision: dict, horizon_hours: int) -> None:
    symbol = decision["symbol"]
    action = decision["action"]
    price_at_signal = float(decision["price_at_signal"])

    price_at_horizon = _current_price(client, symbol)
    actual_return = (price_at_horizon - price_at_signal) / price_at_signal

    # WAIT decisions have no directional bet, so they are never scored "correct"
    correct = (action == "BUY" and actual_return > 0) or (action == "AVOID" and actual_return < 0)

    insert_outcome(
        decision_id=decision["id"],
        horizon_hours=horizon_hours,
        price_at_horizon=price_at_horizon,
        actual_return=actual_return,
        correct=correct,
    )

    logger.info(
        f"decision_id={decision['id']} symbol={symbol} horizon={horizon_hours}h "
        f"action={action} return={actual_return:.4%} correct={correct}"
    )


def run() -> None:
    client = BinanceClient(settings=get_binance_settings())

    for horizon_hours in _HORIZONS_HOURS:
        decisions = get_unevaluated_decisions(horizon_hours)
        logger.info(f"horizon={horizon_hours}h — {len(decisions)} decisions to evaluate")

        for decision in decisions:
            try:
                _evaluate_decision(client, decision, horizon_hours)
            except Exception as exc:
                logger.error(f"failed to evaluate decision_id={decision['id']}: {exc}")


if __name__ == "__main__":
    run()
