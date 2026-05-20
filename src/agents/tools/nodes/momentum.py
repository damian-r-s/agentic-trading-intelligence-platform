from typing import Any

from src.agents.tools.indicators import macd, rsi, bollinger_bands, obv
from src.agents.tools.state import TradingDecisionState
from src.exchanges.binance.market_data import create_binance_market_data_service

def momentum_node(state):
    symbol = state["symbol"]
    service = create_binance_market_data_service()
    candles = service.get_klines(symbol=symbol, interval="1d", limit=250)

    state["momentum"] = _compute_momentum(candles)
    return state

def _compute_momentum(candles: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [c["close"] for c in candles]    
    volumes = [c["volume"] for c in candles]

    rsi_values = rsi(closes, 14)
    current_rsi = float(rsi_values[-1]) # takes today's RSI

    result = macd(closes)
    current_histogram = float(result["histogram"][-1]) # positive indicate bullish momentum

    # Bollinger bands
    bb = bollinger_bands(closes)
    last_price = float(closes[-1])
    upper = float(bb["upper"][-1])
    lower = float(bb["lower"][-1])

    if last_price > upper:
        bb_position = "above_upper"
    elif last_price < lower:
        bb_position = "below_lower"
    else:
        bb_position = "inside"

    # RSI
    if current_rsi > 70:
        rsi_signal = "overbought"
    elif current_rsi < 30: 
        rsi_signal = "oversold"
    else:
        rsi_signal = "neutral"

    # OBV trend - compare last value to N candles ago
    obv_values = obv(closes, volumes)
    if float(obv_values[-1]) > float(obv_values[-10]):
        obv_trend = "rising"
    elif float(obv_values[-1]) < float(obv_values[-10]):
        obv_trend = "falling"
    else:
        obv_trend = "flat"

    # MACD Signal
    if current_histogram > 0:
        macd_signal = "bullish"
    elif current_histogram < 0:
        macd_signal = "bearish"
    else:
        macd_signal = "neutral"

    return {
        "macd_signal": macd_signal,
        "rsi": current_rsi,
        "rsi_signal": rsi_signal,
        "obv_trend": obv_trend,
        "bb_position": bb_position
    }