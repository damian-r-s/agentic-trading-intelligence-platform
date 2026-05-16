from typing import Any, TypedDict


class TradingAgentState(TypedDict, total=False):
    portfolio: dict[str, Any]
    risk_metrics: dict[str, Any]
    analysis: dict[str, Any]
    recommendations: list[str]
