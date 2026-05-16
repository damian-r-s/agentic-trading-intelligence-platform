from src.agents.tools.state import TradingAgentState
from src.exchanges.binance.service import create_binance_portfolio_service


def portfolio_snapshot_node(state: TradingAgentState) -> TradingAgentState:
    service = create_binance_portfolio_service()

    state["portfolio"] = service.get_agent_portfolio_state()

    return state
