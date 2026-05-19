from decimal import Decimal


def sma(closes: list[str], period: int) -> list[str | None]:
    result: list[str | None] = [None] * len(closes)    
    dec = [Decimal(c) for c in closes]
    
    for i in range(period - 1, len(dec)):
        result[i] = _fmt(sum(dec[i - period + 1 : i + 1], Decimal(0)) / period)

    return result


def ema(closes: list[str], period: int) -> list[str | None]:
    result: list[str | None] = [None] * len(closes)    
    
    dec = [Decimal(c) for c in closes]
    
    if len(dec) < period:
        return result

    multiplier = Decimal(2) / (Decimal(period) + 1)
    current = sum(dec[:period], Decimal(0)) / period
    result[period - 1] = _fmt(current)

    for i in range(period, len(dec)):
        current = dec[i] * multiplier + current * (1 - multiplier)
        result[i] = _fmt(current)

    return result


def rsi(closes: list[str], period: int = 14) -> list[str | None]:
    result: list[str | None] = [None] * len(closes)
    dec = [Decimal(c) for c in closes]
    if len(dec) < period + 1:
        return result

    changes = [dec[i] - dec[i - 1] for i in range(1, len(dec))]
    gains = [max(c, Decimal(0)) for c in changes]
    losses = [abs(min(c, Decimal(0))) for c in changes]

    avg_gain = sum(gains[:period], Decimal(0)) / period
    avg_loss = sum(losses[:period], Decimal(0)) / period
    result[period] = _fmt(_rsi_from_averages(avg_gain, avg_loss))

    for i in range(period + 1, len(dec)):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        result[i] = _fmt(_rsi_from_averages(avg_gain, avg_loss))

    return result


def macd(
    closes: list[str],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, list[str | None]]:
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)

    macd_line: list[str | None] = [
        _fmt(Decimal(f) - Decimal(s)) if f is not None and s is not None else None
        for f, s in zip(fast_ema, slow_ema)
    ]

    signal_line: list[str | None] = [None] * len(closes)
    histogram: list[str | None] = [None] * len(closes)

    valid_macd = [v for v in macd_line if v is not None]
    if not valid_macd:
        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    signal_values = ema(valid_macd, signal)

    j = 0
    for i in range(len(closes)):
        if macd_line[i] is not None:
            if signal_values[j] is not None:
                signal_line[i] = signal_values[j]
                histogram[i] = _fmt(Decimal(macd_line[i]) - Decimal(signal_values[j]))
            j += 1

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def bollinger_bands(
    closes: list[str],
    period: int = 20,
    num_std: int = 2,
) -> dict[str, list[str | None]]:
    middle: list[str | None] = [None] * len(closes)
    upper: list[str | None] = [None] * len(closes)
    lower: list[str | None] = [None] * len(closes)

    dec = [Decimal(c) for c in closes]
    for i in range(period - 1, len(dec)):
        window = dec[i - period + 1 : i + 1]
        avg = sum(window, Decimal(0)) / period
        std = (sum((x - avg) ** 2 for x in window) / period).sqrt()
        middle[i] = _fmt(avg)
        upper[i] = _fmt(avg + num_std * std)
        lower[i] = _fmt(avg - num_std * std)

    return {"middle": middle, "upper": upper, "lower": lower}


def atr(
    highs: list[str],
    lows: list[str],
    closes: list[str],
    period: int = 14,
) -> list[str | None]:
    result: list[str | None] = [None] * len(closes)
    if len(closes) < period + 1:
        return result

    h = [Decimal(x) for x in highs]
    l = [Decimal(x) for x in lows]
    c = [Decimal(x) for x in closes]

    true_ranges = [
        max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        for i in range(1, len(c))
    ]

    current = sum(true_ranges[:period], Decimal(0)) / period
    result[period] = _fmt(current)

    for i in range(period + 1, len(c)):
        current = (current * (period - 1) + true_ranges[i - 1]) / period
        result[i] = _fmt(current)

    return result


def obv(closes: list[str], volumes: list[str]) -> list[str]:
    dec_closes = [Decimal(c) for c in closes]
    dec_volumes = [Decimal(v) for v in volumes]

    current = Decimal(0)
    result = ["0"]

    for i in range(1, len(dec_closes)):
        if dec_closes[i] > dec_closes[i - 1]:
            current += dec_volumes[i]
        elif dec_closes[i] < dec_closes[i - 1]:
            current -= dec_volumes[i]
        result.append(_fmt(current))

    return result


def _rsi_from_averages(avg_gain: Decimal, avg_loss: Decimal) -> Decimal:
    if avg_loss == 0:
        return Decimal(100)
    return Decimal(100) - (Decimal(100) / (1 + avg_gain / avg_loss))


def _fmt(d: Decimal) -> str:
    return format(d.normalize(), "f")
