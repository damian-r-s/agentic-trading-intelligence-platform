import json
from src.core.databases.database import get_conn

def upsert_news_article(headline, source, url, published_at, symbol, finbert_score, finbert_label, raw_scores):
    sql = """
        INSERT INTO news_articles
            (headline, source, url, symbol, published_at, finbert_score, finbert_label, raw_scores)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            headline      = EXCLUDED.headline,
            finbert_score = COALESCE(EXCLUDED.finbert_score, news_articles.finbert_score),
            finbert_label = COALESCE(EXCLUDED.finbert_label, news_articles.finbert_label),
            raw_scores    = COALESCE(EXCLUDED.raw_scores,    news_articles.raw_scores)
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (headline, source, url, symbol, published_at,
                  finbert_score, finbert_label,
                  json.dumps(raw_scores) if raw_scores is not None else None))
            return cur.fetchone()[0]
        

def update_finbert(article_id, score, label, raw_scores):
    sql = """
        UPDATE news_articles
        SET finbert_score = %s, finbert_label = %s, raw_scores = %s
        WHERE id = %s
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (score, label, json.dumps(raw_scores), article_id))