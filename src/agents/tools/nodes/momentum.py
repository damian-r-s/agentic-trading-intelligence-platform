from typing import Any

from src.agents.tools.indicators import macd, rsi, bollinger_bands, obv
from src.core.logging import get_logger

logger = get_logger(__name__)

def momentum_node(state):
    symbol = state["symbol"]
    logger.info(f"START symbol={symbol}")

    candles = state["daily_candles"]
    logger.info(f"Using {len(candles)} daily candles from state")

    result = _compute_momentum(candles)
    logger.info(f"RESULT rsi={result['rsi']:.1f} rsi_signal={result['rsi_signal']} macd={result['macd_signal']} obv={result['obv_trend']}")

    return {"momentum": result}

def _compute_momentum(candles: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [c["close"] for c in candles]
    volumes = [c["volume"] for c in candles]

    # RSI — indicator returns None for first `period` elements
    rsi_values = rsi(closes, 14)
    rsi_last = rsi_values[-1]
    current_rsi = float(rsi_last) if rsi_last is not None else 50.0

    # MACD histogram — None until enough candles for signal EMA
    macd_result = macd(closes)
    histogram_last = macd_result["histogram"][-1]
    current_histogram = float(histogram_last) if histogram_last is not None else 0.0

    # Bollinger bands — None for first `period - 1` elements
    bb = bollinger_bands(closes)
    last_price = float(closes[-1])
    upper_last = bb["upper"][-1]
    lower_last = bb["lower"][-1]

    if upper_last is not None and lower_last is not None:
        upper = float(upper_last)
        lower = float(lower_last)
        if last_price > upper:
            bb_position = "above_upper"
        elif last_price < lower:
            bb_position = "below_lower"
        else:
            bb_position = "inside"
    else:
        bb_position = "inside"

    # RSI signal
    if current_rsi > 70:
        rsi_signal = "overbought"
    elif current_rsi < 30:
        rsi_signal = "oversold"
    else:
        rsi_signal = "neutral"

    # OBV trend — compare last value to 10 candles ago
    obv_values = obv(closes, volumes)
    if float(obv_values[-1]) > float(obv_values[-10]):
        obv_trend = "rising"
    elif float(obv_values[-1]) < float(obv_values[-10]):
        obv_trend = "falling"
    else:
        obv_trend = "flat"

    # MACD signal
    if current_histogram > 0:
        macd_signal = "bullish"
    elif current_histogram < 0:
        macd_signal = "bearish"
    else:
        macd_signal = "neutral"

    return {
        "macd_signal": macd_signal,
        "rsi":         current_rsi,
        "rsi_signal":  rsi_signal,
        "obv_trend":   obv_trend,
        "bb_position": bb_position,
    }