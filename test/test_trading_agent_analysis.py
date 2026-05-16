from src.agents.tools.nodes.analysis import analysis_node
from src.agents.tools.nodes.risk_metrics import risk_metrics_node
from src.agents.tools.risk import calculate_risk_metrics


def sample_portfolio():
    return {
        "assets": [
            {
                "asset": "BTC",
                "free": "0.01",
                "locked": "0.005",
                "total": "0.015",
                "trades": [{"side": "BUY"}, {"side": "SELL"}],
                "open_orders": [{"side": "SELL"}],
            },
            {
                "asset": "USDT",
                "free": "100",
                "locked": "0",
                "total": "100",
                "trades": [],
                "open_orders": [],
            },
        ],
        "open_orders": [
            {"side": "SELL"},
            {"side": "BUY"},
        ],
        "trade_fees": [
            {
                "symbol": "BTCUSDT",
                "maker_commission": "0.001",
                "taker_commission": "0.001",
            }
        ],
    }


def test_calculate_risk_metrics():
    metrics = calculate_risk_metrics(sample_portfolio())

    assert metrics["asset_count"] == 2
    assert metrics["open_order_count"] == 2
    assert metrics["open_buy_order_count"] == 1
    assert metrics["open_sell_order_count"] == 1
    assert metrics["locked_asset_count"] == 1
    assert metrics["assets_with_locked_funds"] == ["BTC"]
    assert metrics["trade_counts_by_asset"] == {"BTC": 2, "USDT": 0}
    assert metrics["largest_position_by_units"] == {
        "asset": "USDT",
        "total": "100",
    }


def test_analysis_nodes_add_analysis_and_recommendations():
    state = {"portfolio": sample_portfolio()}

    state = risk_metrics_node(state)
    state = analysis_node(state)

    assert "Portfolio contains 2 active assets" in state["analysis"]["summary"]
    assert state["analysis"]["warnings"]
    assert state["analysis"]["opportunities"]
    assert state["recommendations"] == [
        "Review open orders and locked balances before new trades.",
        "Add live ticker prices to evaluate distance to triggers.",
    ]
