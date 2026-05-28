-- Backtester run metadata, replay trades, and summary metrics

CREATE TABLE IF NOT EXISTS backtest_runs (
    id            BIGSERIAL   PRIMARY KEY,
    strategy_name TEXT        NOT NULL,
    symbol        TEXT        NOT NULL,
    start_date    TIMESTAMPTZ NOT NULL,
    end_date      TIMESTAMPTZ NOT NULL,
    params        JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_backtest_runs_date_range
        CHECK (end_date > start_date)
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id         BIGSERIAL        PRIMARY KEY,
    run_id     BIGINT           NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    symbol     TEXT             NOT NULL,
    side       TEXT             NOT NULL,
    price      NUMERIC(38, 18)  NOT NULL,
    quantity   NUMERIC(38, 18)  NOT NULL,
    traded_at  TIMESTAMPTZ      NOT NULL,
    pnl        NUMERIC(38, 18),
    created_at TIMESTAMPTZ      NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_backtest_trades_side
        CHECK (side IN ('buy', 'sell')),

    CONSTRAINT chk_backtest_trades_price_positive
        CHECK (price > 0),

    CONSTRAINT chk_backtest_trades_quantity_positive
        CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS backtest_results (
    id                BIGSERIAL      PRIMARY KEY,
    run_id            BIGINT         NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    total_return      NUMERIC(18, 8),
    sharpe_ratio      NUMERIC(18, 8),
    max_drawdown      NUMERIC(18, 8),
    hit_rate          NUMERIC(18, 8),
    avg_holding_hours NUMERIC(18, 8),
    total_trades      INTEGER,
    created_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_backtest_results_run_id
        UNIQUE (run_id),

    CONSTRAINT chk_backtest_results_hit_rate
        CHECK (hit_rate IS NULL OR hit_rate BETWEEN 0 AND 1),

    CONSTRAINT chk_backtest_results_total_trades
        CHECK (total_trades IS NULL OR total_trades >= 0)
);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy_symbol
    ON backtest_runs (strategy_name, symbol);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_created_at
    ON backtest_runs (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_run_id
    ON backtest_trades (run_id);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_symbol_traded_at
    ON backtest_trades (symbol, traded_at DESC);

CREATE INDEX IF NOT EXISTS idx_backtest_results_sharpe_ratio
    ON backtest_results (sharpe_ratio DESC);
