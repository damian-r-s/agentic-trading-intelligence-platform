from src.agents.tools.state import TradingDecisionState


def analysis_node(state: TradingDecisionState) -> TradingDecisionState:
    portfolio = state["portfolio"]
    risk_metrics = state["risk_metrics"]

    warnings = build_warnings(risk_metrics)
    opportunities = build_opportunities(portfolio, risk_metrics)

    state["analysis"] = {
        "summary": build_summary(portfolio, risk_metrics),
        "warnings": warnings,
        "opportunities": opportunities,
    }
    state["recommendations"] = build_recommendations(warnings, opportunities)

    return state


def build_summary(
    portfolio: dict,
    risk_metrics: dict,
) -> str:
    return (
        f"Portfolio contains {risk_metrics['asset_count']} active assets, "
        f"{risk_metrics['open_order_count']} open orders, and "
        f"{len(portfolio.get('trade_fees', []))} fee records."
    )


def build_warnings(risk_metrics: dict) -> list[str]:
    warnings = []

    if risk_metrics["locked_asset_count"] > 0:
        assets = ", ".join(risk_metrics["assets_with_locked_funds"])
        warnings.append(f"Locked funds detected for: {assets}.")

    if risk_metrics["open_buy_order_count"] > 0:
        warnings.append("Open buy orders may increase exposure if executed.")

    if risk_metrics["open_sell_order_count"] > 0:
        warnings.append("Open sell orders may reduce current positions if executed.")

    return warnings


def build_opportunities(portfolio: dict, risk_metrics: dict) -> list[str]:
    opportunities = []

    if portfolio.get("trade_fees"):
        opportunities.append("Trade fee data is available for cost-aware decisions.")

    if risk_metrics["open_order_count"] > 0:
        opportunities.append("Open orders can be monitored against live market prices.")

    return opportunities


def build_recommendations(
    warnings: list[str],
    opportunities: list[str],
) -> list[str]:
    recommendations = []

    if warnings:
        recommendations.append("Review open orders and locked balances before new trades.")

    if opportunities:
        recommendations.append("Add live ticker prices to evaluate distance to triggers.")

    if not recommendations:
        recommendations.append("No immediate portfolio risks detected from current state.")

    return recommendations
