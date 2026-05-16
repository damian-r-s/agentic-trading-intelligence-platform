from src.agents.tools.nodes.analysis import analysis_node
from src.agents.tools.nodes.portfolio_snapshot import portfolio_snapshot_node
from src.agents.tools.nodes.risk_metrics import risk_metrics_node
from src.agents.tools.state import TradingAgentState


def run_trading_analysis() -> TradingAgentState:
    state: TradingAgentState = {}

    state = portfolio_snapshot_node(state)
    state = risk_metrics_node(state)
    state = analysis_node(state)

    return state
