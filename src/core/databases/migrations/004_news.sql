-- News & sentiment storage for FinBERT pipeline

CREATE TABLE IF NOT EXISTS news_articles (
    id            BIGSERIAL        PRIMARY KEY,
    headline      TEXT             NOT NULL,
    source        TEXT             NOT NULL,
    url           TEXT             NOT NULL,
    symbol        TEXT,
    published_at  TIMESTAMPTZ      NOT NULL,
    fetched_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    finbert_score DOUBLE PRECISION,
    finbert_label TEXT,
    raw_scores    JSONB,
    
    CONSTRAINT uq_news_articles_url UNIQUE (url),

    CONSTRAINT chk_finbert_label
        CHECK (
            finbert_label IS NULL OR
            finbert_label IN ('positive', 'negative', 'neutral')
        )
);

CREATE INDEX IF NOT EXISTS idx_news_articles_symbol
    ON news_articles (symbol);

CREATE INDEX IF NOT EXISTS idx_news_articles_published_at
    ON news_articles (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_articles_source
    ON news_articles (source);

CREATE INDEX IF NOT EXISTS idx_news_articles_finbert_label
    ON news_articles (finbert_label);

CREATE INDEX IF NOT EXISTS idx_news_articles_symbol_published_at
    ON news_articles (symbol, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_articles_raw_scores_gin
    ON news_articles
    USING GIN (raw_scores);
