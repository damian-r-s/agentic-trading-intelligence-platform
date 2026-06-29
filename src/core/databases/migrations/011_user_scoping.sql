-- Scope analysis runs, portfolio snapshots, and signal metrics to a user.
-- Nullable: pre-existing rows predate multi-user support and stay unowned.
-- trading_decisions/analysis_signals/outcomes are scoped transitively via
-- their existing FK to analysis_runs/trading_decisions.

ALTER TABLE analysis_runs
    ADD COLUMN user_id BIGINT REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE portfolio_snapshots
    ADD COLUMN user_id BIGINT REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE signal_metrics
    ADD COLUMN user_id BIGINT REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_analysis_runs_user_id
    ON analysis_runs (user_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_user_id
    ON portfolio_snapshots (user_id);

CREATE INDEX IF NOT EXISTS idx_signal_metrics_user_id
    ON signal_metrics (user_id);
