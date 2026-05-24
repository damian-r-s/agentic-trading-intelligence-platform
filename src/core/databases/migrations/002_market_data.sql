-- Raw historical market data for ML training and backtesting

CREATE TABLE IF NOT EXISTS candles (
    symbol     TEXT             NOT NULL,
    interval   TEXT             NOT NULL,
    open_time  TIMESTAMPTZ      NOT NULL,
    open       NUMERIC(38, 18)  NOT NULL,
    high       NUMERIC(38, 18)  NOT NULL,
    low        NUMERIC(38, 18)  NOT NULL,
    close      NUMERIC(38, 18)  NOT NULL,
    volume     NUMERIC(38, 18)  NOT NULL,
    created_at TIMESTAMPTZ      NOT NULL DEFAULT NOW(),

    PRIMARY KEY (symbol, interval, open_time)
);

CREATE INDEX IF NOT EXISTS idx_candles_symbol_interval_time
    ON candles (symbol, interval, open_time DESC);

CREATE INDEX IF NOT EXISTS idx_candles_open_time
    ON candles (open_time DESC);
