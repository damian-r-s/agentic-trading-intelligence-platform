from decimal import Decimal

import pytest

from src.agents.tools.indicators import (
    atr,
    bollinger_bands,
    ema,
    macd,
    obv,
    rsi,
    sma,
)

# ---------------------------------------------------------------------------
# SMA
# ---------------------------------------------------------------------------

def test_sma_first_valid_index_is_period_minus_one():
    result = sma(["1", "2", "3", "4", "5"], period=3)

    assert result[0] is None
    assert result[1] is None
    assert result[2] is not None


def test_sma_correct_value():
    # SMA(3) of [1, 2, 3, 4, 5]: last window = [3, 4, 5] → 4
    result = sma(["1", "2", "3", "4", "5"], period=3)

    assert Decimal(result[-1]) == Decimal("4")


def test_sma_period_one_equals_close():
    closes = ["10", "20", "30"]

    assert sma(closes, period=1) == closes


def test_sma_full_series_all_same_value():
    result = sma(["5", "5", "5", "5", "5"], period=3)

    for v in result[2:]:
        assert Decimal(v) == Decimal("5")


def test_sma_returns_none_when_not_enough_data():
    result = sma(["1", "2"], period=5)

    assert all(v is None for v in result)


def test_sma_length_matches_input():
    closes = ["1", "2", "3", "4", "5", "6", "7"]
    assert len(sma(closes, period=4)) == len(closes)


# ---------------------------------------------------------------------------
# EMA
# ---------------------------------------------------------------------------

def test_ema_first_valid_index_is_period_minus_one():
    result = ema(["1", "2", "3", "4", "5"], period=3)

    assert result[0] is None
    assert result[1] is None
    assert result[2] is not None


def test_ema_seed_equals_sma_of_first_period():
    # EMA seed (index period-1) = SMA of first `period` values
    closes = ["10", "20", "30", "40", "50"]
    result = ema(closes, period=3)

    # SMA([10, 20, 30]) = 20
    assert Decimal(result[2]) == Decimal("20")


def test_ema_reacts_faster_than_sma_to_spike():
    # After a big upward spike the EMA should be closer to the spike than SMA
    closes = ["10"] * 10 + ["100"]
    e = ema(closes, period=5)
    s = sma(closes, period=5)

    ema_last = Decimal(e[-1])
    sma_last = Decimal(s[-1])

    assert ema_last > sma_last


def test_ema_constant_series_equals_constant():
    result = ema(["7"] * 10, period=4)

    for v in result[3:]:
        assert Decimal(v) == Decimal("7")


def test_ema_returns_none_when_not_enough_data():
    assert all(v is None for v in ema(["1", "2"], period=5))


def test_ema_length_matches_input():
    closes = ["1", "2", "3", "4", "5", "6", "7"]
    assert len(ema(closes, period=3)) == len(closes)


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------

def test_rsi_first_valid_index_is_period():
    closes = [str(i) for i in range(1, 20)]
    result = rsi(closes, period=14)

    assert result[13] is None
    assert result[14] is not None


def test_rsi_constant_series_returns_none_gain_loss_zero():
    # All closes equal → avg_gain = avg_loss = 0, RSI undefined (returns 100 by convention)
    result = rsi(["50"] * 20, period=14)

    assert result[14] == "100"


def test_rsi_all_up_moves_returns_100():
    # Strictly rising prices → avg_loss = 0 → RSI = 100
    closes = [str(i) for i in range(1, 20)]
    result = rsi(closes, period=14)

    assert result[14] == "100"


def test_rsi_all_down_moves_returns_zero():
    # Strictly falling prices → avg_gain = 0 → RSI = 0
    closes = [str(i) for i in range(20, 0, -1)]
    result = rsi(closes, period=14)

    assert Decimal(result[14]) == Decimal("0")


def test_rsi_value_stays_between_0_and_100():
    closes = ["44", "45", "43", "46", "47", "45", "48", "50", "49", "51",
              "52", "50", "53", "54", "52", "55", "56", "54", "57", "58"]
    result = rsi(closes, period=14)

    for v in result:
        if v is not None:
            assert Decimal("0") <= Decimal(v) <= Decimal("100")


def test_rsi_returns_none_when_not_enough_data():
    assert all(v is None for v in rsi(["1", "2", "3"], period=14))


def test_rsi_length_matches_input():
    closes = [str(i) for i in range(1, 25)]
    assert len(rsi(closes, period=14)) == len(closes)


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def _make_closes(n: int) -> list[str]:
    return [str(40000 + i * 100) for i in range(n)]


def test_macd_returns_three_lists():
    result = macd(_make_closes(40))
    assert set(result.keys()) == {"macd", "signal", "histogram"}


def test_macd_lengths_match_input():
    closes = _make_closes(40)
    result = macd(closes)

    assert len(result["macd"]) == 40
    assert len(result["signal"]) == 40
    assert len(result["histogram"]) == 40


def test_macd_line_first_valid_at_slow_period_minus_one():
    # Default slow=26 → first non-None at index 25
    result = macd(_make_closes(40), fast=12, slow=26, signal=9)

    assert result["macd"][24] is None
    assert result["macd"][25] is not None


def test_macd_signal_requires_extra_candles():
    # MACD line starts at index slow-1 = 25
    # Signal = EMA(9) of MACD → needs 9 more values → first valid at 25 + (9-1) = 33
    result = macd(_make_closes(40), fast=12, slow=26, signal=9)

    assert result["signal"][32] is None
    assert result["signal"][33] is not None  # first valid signal


def test_macd_histogram_is_macd_minus_signal():
    result = macd(_make_closes(50))

    for m, s, h in zip(result["macd"], result["signal"], result["histogram"]):
        if m is not None and s is not None and h is not None:
            assert Decimal(h) == Decimal(m) - Decimal(s)


def test_macd_all_none_when_insufficient_data():
    result = macd(_make_closes(10))

    assert all(v is None for v in result["macd"])
    assert all(v is None for v in result["signal"])
    assert all(v is None for v in result["histogram"])


def test_macd_rising_series_macd_line_is_positive():
    # In a strictly rising series EMA(12) > EMA(26) → MACD > 0
    result = macd(_make_closes(40))

    valid = [v for v in result["macd"] if v is not None]
    assert all(Decimal(v) > 0 for v in valid)


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def test_bollinger_bands_returns_three_keys():
    result = bollinger_bands(["50"] * 25)
    assert set(result.keys()) == {"middle", "upper", "lower"}


def test_bollinger_bands_first_valid_at_period_minus_one():
    result = bollinger_bands(["50"] * 25, period=20)

    assert result["middle"][18] is None
    assert result["middle"][19] is not None


def test_bollinger_bands_middle_equals_sma():
    closes = [str(i) for i in range(1, 30)]
    bb = bollinger_bands(closes, period=20)
    s = sma(closes, period=20)

    for m, sv in zip(bb["middle"], s):
        if m is not None and sv is not None:
            assert Decimal(m) == Decimal(sv)


def test_bollinger_bands_upper_above_middle_above_lower():
    closes = ["50", "52", "48", "51", "53", "49", "50", "52", "54", "48",
              "51", "53", "50", "52", "49", "51", "53", "50", "52", "54",
              "55", "53", "51", "52", "50"]
    result = bollinger_bands(closes, period=20)

    for u, m, l in zip(result["upper"], result["middle"], result["lower"]):
        if u is not None:
            assert Decimal(u) > Decimal(m) > Decimal(l)


def test_bollinger_bands_constant_series_has_zero_width():
    # All closes equal → std = 0 → upper = middle = lower
    result = bollinger_bands(["100"] * 25, period=20)

    for u, m, l in zip(result["upper"], result["middle"], result["lower"]):
        if u is not None:
            assert Decimal(u) == Decimal(m) == Decimal(l)


def test_bollinger_bands_length_matches_input():
    closes = ["50"] * 30
    result = bollinger_bands(closes, period=20)
    assert len(result["middle"]) == 30


# ---------------------------------------------------------------------------
# ATR
# ---------------------------------------------------------------------------

def _make_hlc(n: int, base: int = 100, spread: int = 2) -> tuple[list[str], list[str], list[str]]:
    highs  = [str(base + spread) for _ in range(n)]
    lows   = [str(base - spread) for _ in range(n)]
    closes = [str(base) for _ in range(n)]
    return highs, lows, closes


def test_atr_first_valid_at_period():
    highs, lows, closes = _make_hlc(20)
    result = atr(highs, lows, closes, period=14)

    assert result[13] is None
    assert result[14] is not None


def test_atr_constant_bars_equals_spread():
    # Each candle: high=102, low=98, close=100, prev_close=100
    # TR = max(4, |102-100|, |98-100|) = max(4, 2, 2) = 4
    highs, lows, closes = _make_hlc(20, base=100, spread=2)
    result = atr(highs, lows, closes, period=14)

    for v in result[14:]:
        assert Decimal(v) == Decimal("4")


def test_atr_is_always_positive():
    highs  = ["52", "53", "51", "54", "55", "53", "56", "57", "55", "58",
              "59", "57", "60", "61", "59", "62"]
    lows   = ["48", "49", "47", "50", "51", "49", "52", "53", "51", "54",
              "55", "53", "56", "57", "55", "58"]
    closes = ["50", "51", "49", "52", "53", "51", "54", "55", "53", "56",
              "57", "55", "58", "59", "57", "60"]
    result = atr(highs, lows, closes, period=14)

    for v in result:
        if v is not None:
            assert Decimal(v) > 0


def test_atr_returns_none_when_not_enough_data():
    highs, lows, closes = _make_hlc(5)
    assert all(v is None for v in atr(highs, lows, closes, period=14))


def test_atr_length_matches_input():
    highs, lows, closes = _make_hlc(20)
    assert len(atr(highs, lows, closes, period=14)) == 20


# ---------------------------------------------------------------------------
# OBV
# ---------------------------------------------------------------------------

def test_obv_starts_at_zero():
    result = obv(["100", "101"], ["500", "600"])

    assert result[0] == "0"


def test_obv_adds_volume_on_up_close():
    # close goes up: 100 → 110, volume 200 → OBV = 0 + 200 = 200
    result = obv(["100", "110"], ["500", "200"])

    assert Decimal(result[1]) == Decimal("200")


def test_obv_subtracts_volume_on_down_close():
    # close goes down: 100 → 90, volume 300 → OBV = 0 - 300 = -300
    result = obv(["100", "90"], ["500", "300"])

    assert Decimal(result[1]) == Decimal("-300")


def test_obv_unchanged_on_flat_close():
    result = obv(["100", "100", "100"], ["500", "400", "300"])

    assert result[0] == result[1] == result[2] == "0"


def test_obv_cumulative_sequence():
    # up +200, down -150, up +300
    closes  = ["100", "110", "105", "115"]
    volumes = ["500", "200",  "150", "300"]
    result = obv(closes, volumes)

    assert Decimal(result[0]) == Decimal("0")
    assert Decimal(result[1]) == Decimal("200")    # 0 + 200
    assert Decimal(result[2]) == Decimal("50")     # 200 - 150
    assert Decimal(result[3]) == Decimal("350")    # 50 + 300


def test_obv_length_matches_input():
    closes  = ["100", "101", "99", "102", "98"]
    volumes = ["100",  "200", "150", "250", "180"]

    assert len(obv(closes, volumes)) == len(closes)


def test_obv_always_returns_strings_no_none():
    closes  = ["100", "101", "99"]
    volumes = ["100",  "200", "150"]
    result = obv(closes, volumes)

    assert all(isinstance(v, str) for v in result)
