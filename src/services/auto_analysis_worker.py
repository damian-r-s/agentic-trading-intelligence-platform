from src.agents.tools.graph import run_trading_analysis
from src.core.databases.repositories.users_repo import list_user_ids
from src.core.logging import get_logger

logger = get_logger(__name__)

SYMBOLS = ("BTCUSDT", "SOLUSDT", "ETHUSDT")


def run() -> None:
    for user_id in list_user_ids():
        for symbol in SYMBOLS:
            try:
                result = run_trading_analysis(symbol, user_id)
                decision = result.get("decision_report", {})
                logger.info(
                    f"user_id={user_id} symbol={symbol} "
                    f"action={decision.get('final_action')} confidence={decision.get('confidence')}"
                )
            except Exception as exc:
                logger.error(f"user_id={user_id} symbol={symbol} failed: {exc}")


if __name__ == "__main__":
    run()
