-- ML model registry for HMM, GMM, LSTM, TFT and future models

CREATE TABLE IF NOT EXISTS ml_models (
    id              BIGSERIAL   PRIMARY KEY,

    name            TEXT        NOT NULL,
    model_type      TEXT        NOT NULL,
    version         TEXT        NOT NULL,

    file_path       TEXT        NOT NULL,

    trained_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    training_params JSONB,
    eval_metrics    JSONB,

    is_active       BOOLEAN     NOT NULL DEFAULT FALSE,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_ml_models_name_version
        UNIQUE (name, version),

    CONSTRAINT chk_ml_models_type
        CHECK (model_type IN ('hmm', 'gmm', 'lstm', 'tft'))
);

CREATE INDEX IF NOT EXISTS idx_ml_models_name
    ON ml_models (name);

CREATE INDEX IF NOT EXISTS idx_ml_models_model_type
    ON ml_models (model_type);

CREATE INDEX IF NOT EXISTS idx_ml_models_active
    ON ml_models (is_active);

CREATE INDEX IF NOT EXISTS idx_ml_models_trained_at
    ON ml_models (trained_at DESC);

CREATE INDEX IF NOT EXISTS idx_ml_models_eval_metrics_gin
    ON ml_models
    USING GIN (eval_metrics);

CREATE INDEX IF NOT EXISTS idx_ml_models_training_params_gin
    ON ml_models
    USING GIN (training_params);