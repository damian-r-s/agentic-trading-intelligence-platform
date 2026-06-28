-- Rolling signal-quality metrics (DA / IC / simulated PnL), computed daily per symbol and in aggregate

CREATE TABLE IF NOT EXISTS signal_metrics (
    id                       BIGSERIAL   PRIMARY KEY,
    symbol                   TEXT,        -- NULL = aggregate across all symbols
    horizon_hours            INTEGER     NOT NULL,
    window_days              INTEGER     NOT NULL,
    total_predictions        INTEGER     NOT NULL,
    directional_accuracy     NUMERIC(5, 4),
    information_coefficient  NUMERIC(6, 4),
    simulated_pnl            NUMERIC,
    avg_confidence_correct   NUMERIC(5, 4),
    avg_confidence_incorrect NUMERIC(5, 4),
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_signal_metrics_window
        CHECK (window_days IN (7, 30, 90))
);

CREATE INDEX IF NOT EXISTS idx_signal_metrics_lookup
    ON signal_metrics (symbol, horizon_hours, window_days, computed_at DESC);
