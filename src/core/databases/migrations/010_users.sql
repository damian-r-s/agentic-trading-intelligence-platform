-- User accounts. Binance credentials are stored encrypted (src/core/encryption.py)
-- and are nullable — a user can log in and browse market data before setting one.

CREATE TABLE IF NOT EXISTS users (
    id                      BIGSERIAL   PRIMARY KEY,
    username                TEXT        NOT NULL,
    password_hash           TEXT        NOT NULL,
    binance_api_key_enc     TEXT,
    binance_api_secret_enc  TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_username UNIQUE (username)
);
