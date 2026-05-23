from src.agents.tools.state import TradingDecisionState
from src.core.logging import get_logger
from src.exchanges.binance.service import create_binance_portfolio_service

logger = get_logger(__name__)


def portfolio_snapshot_node(state: TradingDecisionState) -> TradingDecisionState:
    logger.info("START fetching portfolio snapshot...")

    service = create_binance_portfolio_service()
    portfolio = service.get_agent_portfolio_state()

    asset_count = len(portfolio.get("balances", []))
    logger.info(f"RESULT assets={asset_count}")

    state["portfolio"] = portfolio
    return state
