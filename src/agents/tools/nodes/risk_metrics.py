from src.agents.tools.risk import calculate_risk_metrics
from src.agents.tools.state import TradingDecisionState


def risk_metrics_node(state: TradingDecisionState) -> TradingDecisionState:
    state["risk_metrics"] = calculate_risk_metrics(state["portfolio"])

    return state
