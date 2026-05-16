from decimal import Decimal
from typing import Any


def calculate_risk_metrics(portfolio: dict[str, Any]) -> dict[str, Any]:
    assets = portfolio.get("assets", [])
    open_orders = portfolio.get("open_orders", [])

    open_buy_orders = [order for order in open_orders if order.get("side") == "BUY"]
    open_sell_orders = [order for order in open_orders if order.get("side") == "SELL"]
    locked_assets = [
        asset for asset in assets if Decimal(str(asset.get("locked", "0"))) > 0
    ]

    trade_counts_by_asset = {
        asset.get("asset"): len(asset.get("trades", [])) for asset in assets
    }
    largest_position = find_largest_position(assets)

    return {
        "asset_count": len(assets),
        "open_order_count": len(open_orders),
        "open_buy_order_count": len(open_buy_orders),
        "open_sell_order_count": len(open_sell_orders),
        "locked_asset_count": len(locked_assets),
        "assets_with_locked_funds": [asset.get("asset") for asset in locked_assets],
        "trade_counts_by_asset": trade_counts_by_asset,
        "largest_position_by_units": largest_position,
    }


def find_largest_position(assets: list[dict[str, Any]]) -> dict[str, str] | None:
    if not assets:
        return None

    largest = max(assets, key=lambda asset: Decimal(str(asset.get("total", "0"))))

    return {
        "asset": largest.get("asset", ""),
        "total": largest.get("total", "0"),
    }
