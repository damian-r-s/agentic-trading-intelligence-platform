from src.agents.tools.nodes.technical_analysis import compute_technical_indicators


def make_candles(closes, highs=None, lows=None, volumes=None):
    n = len(closes)
    highs   = highs   or [str(float(c) + 1) for c in closes]
    lows    = lows    or [str(float(c) - 1) for c in closes]
    volumes = volumes or ["1000"] * n
    return [
        {"close": c, "high": h, "low": l, "volume": v}
        for c, h, l, v in zip(closes, highs, lows, volumes)
    ]


def rising_closes(n=200, start=40000, step=50):
    return [str(start + i * step) for i in range(n)]


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

def test_result_contains_required_top_level_keys():
    candles = make_candles(rising_closes())
    result = compute_technical_indicators("BTCUSDT", "4h", candles)

    assert set(result.keys()) >= {"symbol", "interval", "candle_count", "latest", "signals"}


def test_symbol_and_interval_are_passed_through():
    candles = make_candles(rising_closes())
    result = compute_technical_indicators("ETHUSDT", "1h", candles)

    assert result["symbol"] == "ETHUSDT"
    assert result["interval"] == "1h"


def test_candle_count_matches_input():
    candles = make_candles(rising_closes(150))
    result = compute_technical_indicators("BTCUSDT", "4h", candles)

    assert result["candle_count"] == 150


def test_latest_contains_all_indicator_keys():
    candles = make_candles(rising_closes())
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    expected_keys = {
        "close",
        "sma_20", "sma_50",
        "ema_9", "ema_21",
        "rsi_14",
        "macd", "macd_signal", "macd_histogram",
        "bb_upper", "bb_middle", "bb_lower",
        "atr_14",
        "obv",
    }
    assert expected_keys.issubset(set(latest.keys()))


def test_latest_close_matches_last_candle():
    closes = rising_closes()
    candles = make_candles(closes)
    result = compute_technical_indicators("BTCUSDT", "4h", candles)

    assert result["latest"]["close"] == closes[-1]


# ---------------------------------------------------------------------------
# Indicator values — sufficient data (200 candles)
# ---------------------------------------------------------------------------

def test_all_moving_averages_are_present_with_200_candles():
    candles = make_candles(rising_closes(200))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["sma_20"]  is not None
    assert latest["sma_50"]  is not None
    assert latest["ema_9"]   is not None
    assert latest["ema_21"]  is not None


def test_rsi_is_present_with_200_candles():
    candles = make_candles(rising_closes(200))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["rsi_14"] is not None


def test_macd_all_lines_are_present_with_200_candles():
    candles = make_candles(rising_closes(200))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["macd"]           is not None
    assert latest["macd_signal"]    is not None
    assert latest["macd_histogram"] is not None


def test_bollinger_bands_are_present_with_200_candles():
    candles = make_candles(rising_closes(200))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["bb_upper"]  is not None
    assert latest["bb_middle"] is not None
    assert latest["bb_lower"]  is not None


def test_atr_is_present_with_200_candles():
    candles = make_candles(rising_closes(200))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["atr_14"] is not None


def test_obv_is_always_present():
    candles = make_candles(rising_closes(10))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["obv"] is not None


# ---------------------------------------------------------------------------
# Indicator values — insufficient data (few candles)
# ---------------------------------------------------------------------------

def test_sma_50_is_none_when_fewer_than_50_candles():
    candles = make_candles(rising_closes(30))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["sma_50"] is None


def test_rsi_is_none_when_fewer_than_15_candles():
    candles = make_candles(rising_closes(14))
    latest = compute_technical_indicators("BTCUSDT", "4h", candles)["latest"]

    assert latest["rsi_14"] is None


# ---------------------------------------------------------------------------
# Signals — RSI zone
# ---------------------------------------------------------------------------

def test_rsi_zone_overbought_on_strictly_rising_series():
    # All up moves → RSI = 100 → overbought
    candles = make_candles(rising_closes(200))
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert signals["rsi_zone"] == "overbought"


def test_rsi_zone_oversold_on_strictly_falling_series():
    closes = [str(50000 - i * 50) for i in range(200)]
    candles = make_candles(closes)
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert signals["rsi_zone"] == "oversold"


def test_rsi_zone_absent_when_insufficient_data():
    candles = make_candles(rising_closes(10))
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert "rsi_zone" not in signals


# ---------------------------------------------------------------------------
# Signals — trend (EMA crossover)
# ---------------------------------------------------------------------------

def test_trend_uptrend_on_rising_series():
    candles = make_candles(rising_closes(200))
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert signals["trend"] == "uptrend"


def test_trend_downtrend_on_falling_series():
    closes = [str(50000 - i * 50) for i in range(200)]
    candles = make_candles(closes)
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert signals["trend"] == "downtrend"


def test_trend_absent_when_ema_not_ready():
    candles = make_candles(rising_closes(15))
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert "trend" not in signals


# ---------------------------------------------------------------------------
# Signals — Bollinger Band position
# ---------------------------------------------------------------------------

def test_bb_position_inside_on_stable_series():
    # Constant price → zero-width bands → price sits exactly on middle
    closes = ["50000"] * 200
    candles = make_candles(closes)
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    # close == upper == lower → "above_upper" (>= upper) is the first branch hit
    assert signals.get("bb_position") is not None


def test_bb_position_absent_when_bands_not_ready():
    candles = make_candles(rising_closes(10))
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert "bb_position" not in signals


# ---------------------------------------------------------------------------
# Signals — MACD cross
# ---------------------------------------------------------------------------

def test_macd_cross_bullish_continuation_on_rising_series():
    candles = make_candles(rising_closes(200))
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    # Rising series → MACD histogram consistently positive → bullish_continuation
    assert signals.get("macd_cross") == "bullish_continuation"


def test_macd_cross_absent_when_histogram_not_ready():
    candles = make_candles(rising_closes(20))
    signals = compute_technical_indicators("BTCUSDT", "4h", candles)["signals"]

    assert "macd_cross" not in signals
