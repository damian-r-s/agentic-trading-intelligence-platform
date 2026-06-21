ALTER TABLE trading_decisions
    ADD COLUMN price_at_signal NUMERIC;

CREATE TABLE IF NOT EXISTS outcomes (
    id                BIGSERIAL    PRIMARY KEY,
    decision_id       BIGINT       NOT NULL REFERENCES trading_decisions(id) ON DELETE CASCADE,
    horizon_hours     INTEGER      NOT NULL,
    price_at_horizon  NUMERIC,
    actual_return     NUMERIC,
    correct           BOOLEAN,
    evaluated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_outcomes_decision_horizon UNIQUE (decision_id, horizon_hours)
);

CREATE INDEX IF NOT EXISTS idx_outcomes_decision_id
    ON outcomes (decision_id);
