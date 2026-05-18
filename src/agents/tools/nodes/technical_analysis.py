from typing import Any

from src.agents.tools.indicators import atr, bollinger_bands, ema, macd, obv, rsi, sma
from src.agents.tools.state import TradingDecisionState
from src.exchanges.binance.market_data import create_binance_market_data_service


def technical_analysis_node(
    state: TradingDecisionState,
    interval: str = "4h",
    limit: int = 500,
) -> TradingDecisionState:
    symbol = state["symbol"]
    service = create_binance_market_data_service()
    candles = service.get_klines(symbol, interval=interval, limit=limit)
    state["technical_analysis"] = compute_technical_indicators(symbol, interval, candles)
    return state


def compute_technical_indicators(
    symbol: str,
    interval: str,
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    closes  = [c["close"]  for c in candles]
    highs   = [c["high"]   for c in candles]
    lows    = [c["low"]    for c in candles]
    volumes = [c["volume"] for c in candles]

    macd_result = macd(closes)
    bb          = bollinger_bands(closes, period=20)
    atr_series  = atr(highs, lows, closes, period=14)
    obv_series  = obv(closes, volumes)

    latest: dict[str, Any] = {
        "close":          closes[-1],
        "sma_20":         sma(closes, 20)[-1],
        "sma_50":         sma(closes, 50)[-1],
        "ema_9":          ema(closes, 9)[-1],
        "ema_21":         ema(closes, 21)[-1],
        "rsi_14":         rsi(closes, 14)[-1],
        "macd":           macd_result["macd"][-1],
        "macd_signal":    macd_result["signal"][-1],
        "macd_histogram": macd_result["histogram"][-1],
        "bb_upper":       bb["upper"][-1],
        "bb_middle":      bb["middle"][-1],
        "bb_lower":       bb["lower"][-1],
        "atr_14":         atr_series[-1],
        "obv":            obv_series[-1],
    }

    return {
        "symbol":       symbol,
        "interval":     interval,
        "candle_count": len(candles),
        "latest":       latest,
        "signals":      _derive_signals(latest, macd_result["histogram"]),
    }


def _derive_signals(
    latest: dict[str, Any],
    macd_histogram: list[str | None],
) -> dict[str, str]:
    signals: dict[str, str] = {}

    # RSI zone
    if latest["rsi_14"] is not None:
        r = float(latest["rsi_14"])
        if r >= 70:
            signals["rsi_zone"] = "overbought"
        elif r <= 30:
            signals["rsi_zone"] = "oversold"
        else:
            signals["rsi_zone"] = "neutral"

    # MACD histogram direction (cross detection)
    current_hist = latest["macd_histogram"]
    prev_hist = next(
        (v for v in reversed(macd_histogram[:-1]) if v is not None), None
    )
    if current_hist is not None and prev_hist is not None:
        c, p = float(current_hist), float(prev_hist)
        if c > 0 and p <= 0:
            signals["macd_cross"] = "bullish"
        elif c < 0 and p >= 0:
            signals["macd_cross"] = "bearish"
        elif c > 0:
            signals["macd_cross"] = "bullish_continuation"
        else:
            signals["macd_cross"] = "bearish_continuation"

    # Bollinger band position
    if latest["bb_upper"] is not None:
        close = float(latest["close"])
        if close >= float(latest["bb_upper"]):
            signals["bb_position"] = "above_upper"
        elif close <= float(latest["bb_lower"]):
            signals["bb_position"] = "below_lower"
        else:
            signals["bb_position"] = "inside"

    # Trend via EMA-9 / EMA-21 crossover
    if latest["ema_9"] is not None and latest["ema_21"] is not None:
        if float(latest["ema_9"]) > float(latest["ema_21"]):
            signals["trend"] = "uptrend"
        elif float(latest["ema_9"]) < float(latest["ema_21"]):
            signals["trend"] = "downtrend"
        else:
            signals["trend"] = "sideways"

    return signals
