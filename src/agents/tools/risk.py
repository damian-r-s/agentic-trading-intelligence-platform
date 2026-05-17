from decimal import Decimal
from typing import Any


def calculate_risk_metrics(portfolio: dict[str, Any]) -> dict[str, Any]:
    assets = portfolio.get("assets", [])
    open_orders = portfolio.get("open_orders", [])
    current_prices = {
        k: Decimal(str(v)) for k, v in portfolio.get("current_prices", {}).items()
    }

    open_buy_orders = [o for o in open_orders if o.get("side") == "BUY"]
    open_sell_orders = [o for o in open_orders if o.get("side") == "SELL"]
    locked_assets = [
        asset for asset in assets if Decimal(str(asset.get("locked", "0"))) > 0
    ]

    trade_counts_by_asset = {
        asset.get("asset"): len(asset.get("trades", [])) for asset in assets
    }

    position_values_usdt = _compute_position_values(assets, current_prices)
    total_portfolio_value = sum(position_values_usdt.values())

    concentration_pct = {}
    if total_portfolio_value > 0:
        concentration_pct = {
            name: round(float(v / total_portfolio_value * 100), 2)
            for name, v in position_values_usdt.items()
        }

    # Herfindahl-Hirschman Index: 0 = fully diversified, 1 = fully concentrated
    hhi = round(sum((pct / 100) ** 2 for pct in concentration_pct.values()), 4)

    locked_value_usdt = sum(
        Decimal(str(a.get("locked", "0"))) * current_prices.get(a.get("asset", ""), Decimal("0"))
        for a in assets
    )
    locked_ratio = (
        round(float(locked_value_usdt / total_portfolio_value), 4)
        if total_portfolio_value > 0
        else 0.0
    )

    open_buy_orders_value = sum(
        Decimal(str(o.get("price", "0"))) * (
            Decimal(str(o.get("original_quantity", "0")))
            - Decimal(str(o.get("executed_quantity", "0")))
        )
        for o in open_buy_orders
    )

    pnl = _compute_pnl(assets, current_prices)

    return {
        "asset_count": len(assets),
        "open_order_count": len(open_orders),
        "open_buy_order_count": len(open_buy_orders),
        "open_sell_order_count": len(open_sell_orders),
        "locked_asset_count": len(locked_assets),
        "assets_with_locked_funds": [a.get("asset") for a in locked_assets],
        "trade_counts_by_asset": trade_counts_by_asset,
        "largest_position_by_units": find_largest_position(assets),
        "total_portfolio_value_usdt": str(total_portfolio_value),
        "position_values_usdt": {k: str(v) for k, v in position_values_usdt.items()},
        "concentration_pct": concentration_pct,
        "hhi": hhi,
        "largest_position_by_value": _find_largest_by_value(position_values_usdt),
        "locked_value_usdt": str(locked_value_usdt),
        "locked_ratio": locked_ratio,
        "open_buy_orders_value_usdt": str(open_buy_orders_value),
        "unrealized_pnl_by_asset": pnl["unrealized"],
        "total_unrealized_pnl_usdt": pnl["total_unrealized_pnl_usdt"],
        "realized_pnl_by_asset": pnl["realized"],
        "total_realized_pnl_usdt": pnl["total_realized_pnl_usdt"],
    }


def find_largest_position(assets: list[dict[str, Any]]) -> dict[str, str] | None:
    if not assets:
        return None

    largest = max(assets, key=lambda a: Decimal(str(a.get("total", "0"))))

    return {
        "asset": largest.get("asset", ""),
        "total": largest.get("total", "0"),
    }


def _compute_position_values(
    assets: list[dict[str, Any]],
    current_prices: dict[str, Decimal],
) -> dict[str, Decimal]:
    return {
        a.get("asset", ""): Decimal(str(a.get("total", "0")))
        * current_prices.get(a.get("asset", ""), Decimal("0"))
        for a in assets
    }


def _find_largest_by_value(
    position_values_usdt: dict[str, Decimal],
) -> dict[str, str] | None:
    if not position_values_usdt:
        return None

    name = max(position_values_usdt, key=lambda k: position_values_usdt[k])

    return {"asset": name, "value_usdt": str(position_values_usdt[name])}


def _compute_pnl(
    assets: list[dict[str, Any]],
    current_prices: dict[str, Decimal],
) -> dict[str, Any]:
    unrealized: dict[str, Any] = {}
    realized: dict[str, Any] = {}
    total_unrealized = Decimal("0")
    total_realized = Decimal("0")

    for asset_data in assets:
        name = asset_data.get("asset", "")
        trades = asset_data.get("trades", [])

        # Only trades where this asset is the base (i.e., we bought/sold this asset)
        base_trades = sorted(
            [t for t in trades if t.get("base_asset") == name],
            key=lambda t: t.get("time", 0),
        )
        if not base_trades:
            continue

        total_units = Decimal("0")
        total_cost_usdt = Decimal("0")
        realized_pnl_usdt = Decimal("0")

        for trade in base_trades:
            qty = Decimal(str(trade.get("quantity", "0")))
            price = Decimal(str(trade.get("price", "0")))
            quote_asset = trade.get("quote_asset", "")
            quote_to_usdt = current_prices.get(quote_asset, Decimal("1"))
            price_usdt = price * quote_to_usdt

            if trade.get("side") == "BUY":
                total_cost_usdt += qty * price_usdt
                total_units += qty
            elif trade.get("side") == "SELL" and total_units > 0:
                avg_cost_usdt = total_cost_usdt / total_units
                realized_pnl_usdt += (price_usdt - avg_cost_usdt) * qty
                sell_fraction = min(qty / total_units, Decimal("1"))
                total_cost_usdt *= Decimal("1") - sell_fraction
                total_units = max(total_units - qty, Decimal("0"))
                if total_units == 0:
                    total_cost_usdt = Decimal("0")

        if realized_pnl_usdt != 0:
            realized[name] = {"realized_pnl_usdt": str(realized_pnl_usdt)}
            total_realized += realized_pnl_usdt

        current_units = Decimal(str(asset_data.get("total", "0")))
        current_price = current_prices.get(name, Decimal("0"))
        avg_cost_usdt = total_cost_usdt / total_units if total_units > 0 else Decimal("0")

        if current_price > 0 and avg_cost_usdt > 0:
            unrealized_pnl = (current_price - avg_cost_usdt) * current_units
            pnl_pct = round(
                float((current_price - avg_cost_usdt) / avg_cost_usdt * 100), 2
            )
            unrealized[name] = {
                "avg_cost_basis_usdt": str(avg_cost_usdt),
                "current_price_usdt": str(current_price),
                "unrealized_pnl_usdt": str(unrealized_pnl),
                "unrealized_pnl_pct": pnl_pct,
            }
            total_unrealized += unrealized_pnl

    return {
        "unrealized": unrealized,
        "realized": realized,
        "total_unrealized_pnl_usdt": str(total_unrealized),
        "total_realized_pnl_usdt": str(total_realized),
    }
