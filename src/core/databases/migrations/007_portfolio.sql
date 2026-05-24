-- Portfolio history snapshots

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id               BIGSERIAL       PRIMARY KEY,

    snapshot_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    balances         JSONB           NOT NULL,

    total_value_usdt NUMERIC(38, 18) NOT NULL,

    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_portfolio_total_value_positive
        CHECK (total_value_usdt >= 0)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_snapshot_at
    ON portfolio_snapshots (snapshot_at DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_total_value
    ON portfolio_snapshots (total_value_usdt);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_balances_gin
    ON portfolio_snapshots
    USING GIN (balances);
