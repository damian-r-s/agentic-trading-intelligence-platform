from src.agents.tools.nodes.analysis import analysis_node
from src.agents.tools.nodes.portfolio_snapshot import portfolio_snapshot_node
from src.agents.tools.nodes.risk_metrics import risk_metrics_node
from src.agents.tools.nodes.technical_analysis import technical_analysis_node
from src.agents.tools.state import TradingAgentState


def run_trading_analysis(symbol: str) -> TradingAgentState:
    state: TradingAgentState = {"symbol": symbol}

    state = portfolio_snapshot_node(state)
    state = risk_metrics_node(state)
    state = technical_analysis_node(state, interval="4h", limit=500)
    state = analysis_node(state)

    return state
