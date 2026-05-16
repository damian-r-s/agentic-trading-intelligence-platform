from src.agents.tools.risk import calculate_risk_metrics
from src.agents.tools.state import TradingAgentState


def risk_metrics_node(state: TradingAgentState) -> TradingAgentState:
    state["risk_metrics"] = calculate_risk_metrics(state["portfolio"])

    return state
