-- Cache layer for Binance/API data

CREATE TABLE IF NOT EXISTS cache_exchange_info (
    id         SERIAL      PRIMARY KEY,
    data       JSONB       NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS cache_klines (
    id         SERIAL      PRIMARY KEY,
    symbol     TEXT        NOT NULL,
    interval   TEXT        NOT NULL,
    data       JSONB       NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT uq_cache_klines_symbol_interval UNIQUE (symbol, interval)
);

CREATE TABLE IF NOT EXISTS cache_order_book (
    id         SERIAL      PRIMARY KEY,
    symbol     TEXT        NOT NULL,
    data       JSONB       NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cache_exchange_info_expires_at
    ON cache_exchange_info (expires_at);

CREATE INDEX IF NOT EXISTS idx_cache_klines_symbol_interval_expires_at
    ON cache_klines (symbol, interval, expires_at);

CREATE INDEX IF NOT EXISTS idx_cache_order_book_symbol_expires_at
    ON cache_order_book (symbol, expires_at);
