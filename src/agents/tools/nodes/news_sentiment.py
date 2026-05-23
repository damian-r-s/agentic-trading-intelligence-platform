from typing import Any
import requests
from transformers import pipeline

from src.agents.tools.state import TradingDecisionState
from src.core.config import get_news_settings

_settings = get_news_settings()

_finbert = pipeline(
    task="text-classification",
    model="ProsusAI/finbert",
    top_k=None
)

def _fetch_coingecko(coin_id: str, limit: int = 5) -> list[str]:
    url = "https://api.coingecko.com/api/v3/news"
    response = requests.get(url=url, timeout=10)
    response.raise_for_status()

    articles = response.json().get("data", [])
    headlines = [a["title"] for a in articles if "title" in a]
    return headlines[:limit]

def _fetch_news(query: str, limit: int = 5) -> list[str]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": _settings.news_api_key
    }

    response = requests.get(url=url, params=params, timeout=10)
    response.raise_for_status()

    articles = response.json().get("articles", [])
    headlines = [a["title"] for a in articles if a.get("title")]
    return headlines[:limit]

def _score_headlines(headlines: list[str]) -> tuple[float, list[dict]]:
    if not headlines:
        return 0.0, []
    
    scored = []
    total_score = 0.0

    for headline in headlines:
        results = _finbert([headline])[0]
        scores = { r["label"]: r["score"] for r in results}

        sentiment_score = scores.get("positive", 0.0) - scores.get("negative", 0.0)
        total_score += sentiment_score
        
        scored.append({
            "headline": headline,
            "positive": round(scores.get("positive", 0.0), 3),
            "negative": round(scores.get("negative", 0.0), 3),
            "neutral":  round(scores.get("neutral",  0.0), 3),
            "score":    round(sentiment_score, 3),
        })

    avg_score = round(total_score / len(headlines), 3)
    return avg_score, scored

def sentiment_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state["symbol"]                          # np. "BTCUSDT"
    coin   = symbol.replace("USDT", "").lower()      # → "btc"
    query  = f"{coin} cryptocurrency"                # → "btc cryptocurrency"

    crypto_headlines = _fetch_coingecko(coin)
    macro_headlines  = _fetch_news(query)

    crypto_score, crypto_scored = _score_headlines(crypto_headlines)
    macro_score,  macro_scored  = _score_headlines(macro_headlines)

    combined_score = round(crypto_score * 0.6 + macro_score * 0.4, 3)

    if combined_score > 0.1:
        signal = "bullish"
    elif combined_score < -0.1:
        signal = "bearish"
    else:
        signal = "neutral"

    state["news_sentiment"] = {
        "crypto_headlines": crypto_scored,
        "macro_headlines":  macro_scored,
        "crypto_score":     crypto_score,
        "macro_score":      macro_score,
        "combined_score":   combined_score,
        "signal":           signal,
    }
    return state