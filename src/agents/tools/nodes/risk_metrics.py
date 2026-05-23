from src.agents.tools.risk import calculate_risk_metrics
from src.agents.tools.state import TradingDecisionState
from src.core.logging import get_logger

logger = get_logger(__name__)


def risk_metrics_node(state: TradingDecisionState) -> TradingDecisionState:
    logger.info("START computing risk metrics...")

    result = calculate_risk_metrics(state["portfolio"])
    logger.info(f"RESULT assets={result.get('asset_count')} open_orders={result.get('open_order_count')} locked={result.get('locked_asset_count')}")

    state["risk_metrics"] = result
    return state
