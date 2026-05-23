from typing import Any

from src.agents.tools.state import TradingDecisionState
from src.core.logging import get_logger
from src.exchanges.binance.market_data import create_binance_market_data_service

logger = get_logger(__name__)


def liquidity_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state["symbol"]
    logger.info(f"START symbol={symbol}")

    service = create_binance_market_data_service()
    logger.info("Fetching order book and 24h stats...")
    order_book = service.get_order_book(symbol)
    stats = service.get_24h_stats(symbol)

    result = compute_liquidity(order_book, stats)
    logger.info(f"RESULT spread={result['spread_pct']:.4f}% depth_bias={result['depth_bias']} volume_24h={result['volume_24h']}")

    return {"liquidity": result}


def compute_liquidity(order_book: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    spread_pct = float(order_book["spread_pct"])
    if spread_pct < 0.05:
        spread_signal = "tight"
    elif spread_pct > 0.2:
        spread_signal = "wide"
    else:
        spread_signal = "normal"

    bid = float(order_book["bid_depth"])
    ask = float(order_book["ask_depth"])

    if bid > ask * 1.2:
        depth_bias = "buy_pressure"
    elif ask > bid * 1.2:
        depth_bias = "sell_pressure"
    else:
        depth_bias = "balanced"

    return {
        "spread_pct":           spread_pct,
        "spread_signal":        spread_signal,
        "bid_depth":            order_book["bid_depth"],
        "ask_depth":            order_book["ask_depth"],
        "depth_bias":           depth_bias,
        "volume_24h":           stats["quote_volume"],
        "trade_count":          int(stats["trade_count"]),
        "price_change_pct_24h": stats["price_change_pct"],
    }