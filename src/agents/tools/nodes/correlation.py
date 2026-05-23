import numpy as np

from typing import Any
from src.core.logging import get_logger
from src.exchanges.binance.market_data import create_binance_market_data_service

logger = get_logger(__name__)

def correlation_node(state):
    symbol = state["symbol"]
    logger.info(f"START symbol={symbol}")

    service = create_binance_market_data_service()
    logger.info("Fetching 90d candles for symbol, BTC, ETH...")
    symbol_candles = service.get_klines(symbol=symbol, interval="1d", limit=90)
    btc_candles = service.get_klines(symbol="BTCUSDT", interval="1d", limit=90)
    eth_candles = service.get_klines(symbol="ETHUSDT", interval="1d", limit=90)

    closes_symbol = [c["close"] for c in symbol_candles]
    closes_btc = [c["close"] for c in btc_candles]
    closes_eth = [c["close"] for c in eth_candles]

    btc_corr = float(np.corrcoef(closes_symbol, closes_btc)[0, 1])
    eth_corr = float(np.corrcoef(closes_symbol, closes_eth)[0, 1])
    avg_corr = (abs(btc_corr) + abs(eth_corr)) / 2
    diversification_benefit = _correlation_label(1 - avg_corr)

    logger.info(f"RESULT btc_corr={btc_corr:.3f} eth_corr={eth_corr:.3f} diversification={diversification_benefit}")

    state["correlation"] = {
        "btc_correlation": btc_corr,
        "eth_correlation": eth_corr,
        "btc_correlation_label": _correlation_label(btc_corr),
        "eth_correlation_label": _correlation_label(eth_corr),
        "diversification_benefit": diversification_benefit
    }
    return state

def _correlation_label(correlation: float) -> str:
    if abs(correlation) > 0.8:
        return "high"
    elif abs(correlation) > 0.5:
        return "moderate"
    else:
        return "low"
