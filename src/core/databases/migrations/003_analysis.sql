-- Agent pipeline outputs and final strategy decisions

CREATE TABLE IF NOT EXISTS analysis_runs (
    id           BIGSERIAL   PRIMARY KEY,
    symbol       TEXT        NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status       TEXT        NOT NULL DEFAULT 'running',

    CONSTRAINT chk_analysis_runs_status
        CHECK (status IN ('running', 'done', 'error'))
);

CREATE TABLE IF NOT EXISTS analysis_signals (
    id         BIGSERIAL   PRIMARY KEY,
    run_id     BIGINT      NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    node_name  TEXT        NOT NULL,
    output     JSONB       NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading_decisions (
    id         BIGSERIAL      PRIMARY KEY,
    run_id     BIGINT         NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    action     TEXT           NOT NULL,
    confidence NUMERIC(5, 4),
    entry_zone JSONB,
    thesis     TEXT,
    risks      JSONB,
    created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_trading_decisions_run_id UNIQUE (run_id),

    CONSTRAINT chk_trading_decision
        CHECK (action IN ('BUY', 'WAIT', 'AVOID')),

    CONSTRAINT chk_trading_decisions_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1)
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_symbol_triggered_at
    ON analysis_runs (symbol, triggered_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_status
    ON analysis_runs (status);

CREATE INDEX IF NOT EXISTS idx_analysis_signals_run_id
    ON analysis_signals (run_id);

CREATE INDEX IF NOT EXISTS idx_analysis_signals_node_name
    ON analysis_signals (node_name);

CREATE INDEX IF NOT EXISTS idx_trading_decisions_action
    ON trading_decisions (action);