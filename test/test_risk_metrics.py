from decimal import Decimal

from src.agents.tools.risk import calculate_risk_metrics, find_largest_position


def make_portfolio(assets, open_orders=None, current_prices=None):
    return {
        "assets": assets,
        "open_orders": open_orders or [],
        "current_prices": current_prices or {},
    }


def make_asset(name, total, locked="0", trades=None, open_orders=None):
    free = str(Decimal(total) - Decimal(locked))
    return {
        "asset": name,
        "free": free,
        "locked": locked,
        "total": total,
        "trades": trades or [],
        "open_orders": open_orders or [],
    }


def make_trade(base, quote, side, price, quantity, time=1000):
    return {
        "base_asset": base,
        "quote_asset": quote,
        "side": side,
        "price": price,
        "quantity": quantity,
        "time": time,
    }


# ---------------------------------------------------------------------------
# Portfolio value and concentration
# ---------------------------------------------------------------------------

def test_total_portfolio_value_sums_positions_in_usdt():
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1"),
            make_asset("USDT", "20000"),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["total_portfolio_value_usdt"] == "80000"
    assert metrics["position_values_usdt"]["BTC"] == "60000"
    assert metrics["position_values_usdt"]["USDT"] == "20000"


def test_concentration_pct_sums_to_100():
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1"),
            make_asset("USDT", "20000"),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["concentration_pct"]["BTC"] == 75.0
    assert metrics["concentration_pct"]["USDT"] == 25.0
    assert abs(sum(metrics["concentration_pct"].values()) - 100.0) < 0.01


def test_hhi_for_two_asset_portfolio():
    # 75% BTC, 25% USDT → HHI = 0.75² + 0.25² = 0.5625 + 0.0625 = 0.625
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1"),
            make_asset("USDT", "20000"),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["hhi"] == 0.625


def test_hhi_is_one_for_single_asset():
    portfolio = make_portfolio(
        assets=[make_asset("BTC", "1")],
        current_prices={"BTC": "60000"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["hhi"] == 1.0


def test_largest_position_by_value():
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1"),
            make_asset("USDT", "20000"),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["largest_position_by_value"] == {"asset": "BTC", "value_usdt": "60000"}


def test_no_prices_produces_zero_portfolio_value():
    portfolio = make_portfolio(assets=[make_asset("BTC", "1")])

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["total_portfolio_value_usdt"] == "0"
    assert metrics["concentration_pct"] == {}
    assert metrics["hhi"] == 0.0


# ---------------------------------------------------------------------------
# Unrealized P&L
# ---------------------------------------------------------------------------

def test_unrealized_pnl_when_price_is_above_cost_basis():
    # Bought 1 BTC @ 50000, now at 60000 → unrealized = +10000 (+20%)
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1", trades=[
                make_trade("BTC", "USDT", "BUY", "50000", "1"),
            ]),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)
    pnl = metrics["unrealized_pnl_by_asset"]["BTC"]

    assert pnl["avg_cost_basis_usdt"] == "50000"
    assert pnl["current_price_usdt"] == "60000"
    assert Decimal(pnl["unrealized_pnl_usdt"]) == Decimal("10000")
    assert pnl["unrealized_pnl_pct"] == 20.0


def test_unrealized_pnl_when_price_is_below_cost_basis():
    # Bought 1 BTC @ 70000, now at 60000 → unrealized = -10000 (-14.29%)
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1", trades=[
                make_trade("BTC", "USDT", "BUY", "70000", "1"),
            ]),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)
    pnl = metrics["unrealized_pnl_by_asset"]["BTC"]

    assert Decimal(pnl["unrealized_pnl_usdt"]) == Decimal("-10000")
    assert pnl["unrealized_pnl_pct"] == round(-10000 / 70000 * 100, 2)


def test_no_unrealized_pnl_without_prices():
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1", trades=[
                make_trade("BTC", "USDT", "BUY", "50000", "1"),
            ]),
        ],
        current_prices={},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["unrealized_pnl_by_asset"] == {}


# ---------------------------------------------------------------------------
# Realized P&L
# ---------------------------------------------------------------------------

def test_realized_pnl_profitable_sell():
    # Bought 2 BTC @ 40000, sold 1 @ 50000 → realized = +10000
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1", trades=[
                make_trade("BTC", "USDT", "BUY", "40000", "2", time=1000),
                make_trade("BTC", "USDT", "SELL", "50000", "1", time=2000),
            ]),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert Decimal(metrics["realized_pnl_by_asset"]["BTC"]["realized_pnl_usdt"]) == Decimal("10000")
    assert Decimal(metrics["total_realized_pnl_usdt"]) == Decimal("10000")


def test_realized_pnl_loss_sell():
    # Bought 1 BTC @ 60000, sold @ 50000 → realized = -10000
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "0", trades=[
                make_trade("BTC", "USDT", "BUY", "60000", "1", time=1000),
                make_trade("BTC", "USDT", "SELL", "50000", "1", time=2000),
            ]),
        ],
        current_prices={"BTC": "55000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert Decimal(metrics["realized_pnl_by_asset"]["BTC"]["realized_pnl_usdt"]) == Decimal("-10000")


def test_remaining_cost_basis_after_partial_sell():
    # Bought 2 BTC @ 40000, sold 1 → remaining avg cost should still be 40000
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1", trades=[
                make_trade("BTC", "USDT", "BUY", "40000", "2", time=1000),
                make_trade("BTC", "USDT", "SELL", "50000", "1", time=2000),
            ]),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)
    pnl = metrics["unrealized_pnl_by_asset"]["BTC"]

    # Remaining 1 BTC still costs 40000, now at 60000
    assert pnl["avg_cost_basis_usdt"] == "40000"
    assert Decimal(pnl["unrealized_pnl_usdt"]) == Decimal("20000")


def test_no_realized_pnl_without_sells():
    portfolio = make_portfolio(
        assets=[
            make_asset("BTC", "1", trades=[
                make_trade("BTC", "USDT", "BUY", "50000", "1"),
            ]),
        ],
        current_prices={"BTC": "60000", "USDT": "1"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["realized_pnl_by_asset"] == {}
    assert metrics["total_realized_pnl_usdt"] == "0"


# ---------------------------------------------------------------------------
# Locked funds
# ---------------------------------------------------------------------------

def test_locked_value_and_ratio():
    # 1 BTC total, 0.5 locked → locked_value = 30000, locked_ratio = 0.5
    portfolio = make_portfolio(
        assets=[make_asset("BTC", "1", locked="0.5")],
        current_prices={"BTC": "60000"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["locked_value_usdt"] == "30000"
    assert metrics["locked_ratio"] == 0.5


def test_locked_ratio_is_zero_when_nothing_locked():
    portfolio = make_portfolio(
        assets=[make_asset("BTC", "1", locked="0")],
        current_prices={"BTC": "60000"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["locked_ratio"] == 0.0


# ---------------------------------------------------------------------------
# Open buy orders
# ---------------------------------------------------------------------------

def test_open_buy_order_value_uses_remaining_quantity():
    # Order: buy 0.1 BTC @ 50000, already filled 0.04 → remaining 0.06 → value 3000
    portfolio = make_portfolio(
        assets=[make_asset("BTC", "0")],
        open_orders=[
            {
                "side": "BUY",
                "price": "50000",
                "original_quantity": "0.1",
                "executed_quantity": "0.04",
            }
        ],
        current_prices={"BTC": "60000"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert Decimal(metrics["open_buy_orders_value_usdt"]) == Decimal("3000")


def test_sell_orders_do_not_count_toward_buy_order_value():
    portfolio = make_portfolio(
        assets=[make_asset("BTC", "1")],
        open_orders=[
            {"side": "SELL", "price": "70000", "original_quantity": "1", "executed_quantity": "0"}
        ],
        current_prices={"BTC": "60000"},
    )

    metrics = calculate_risk_metrics(portfolio)

    assert metrics["open_buy_orders_value_usdt"] == "0"


# ---------------------------------------------------------------------------
# find_largest_position
# ---------------------------------------------------------------------------

def test_find_largest_position_by_units():
    assets = [
        make_asset("BTC", "0.01"),
        make_asset("USDT", "1000"),
    ]

    result = find_largest_position(assets)

    assert result == {"asset": "USDT", "total": "1000"}


def test_find_largest_position_returns_none_for_empty_list():
    assert find_largest_position([]) is None
