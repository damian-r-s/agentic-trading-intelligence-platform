import requests

from src.core.logging import get_logger
from fastapi import APIRouter
from transformers import pipeline
import xml.etree.ElementTree as ET

from src.core.config import get_finbert_settings, get_news_settings

logger = get_logger(__name__)

_settings = get_news_settings()
_finbert_settings = get_finbert_settings()

logger.info(f"Loading FinBERT model ({_finbert_settings.model})...")
_finbert = pipeline(task="text-classification", model=_finbert_settings.model, top_k=None)
logger.info("FinBERT ready.")

router = APIRouter(tags=["score"])

@router.get("/score")
async def score(symbol: str, coin: str):    
    logger.info(f"Start symbol={symbol} coin={coin}")
    
    query = f"{coin} cryptocurrency"

    logger.info("Fetching news rss headlines...")
    crypto_headlines = _fetch_coin_desk_rss(coin)
    logger.info(f"Got {len(crypto_headlines)} crypto headlines")

    logger.info(f"Fetching NewsAPI headlines for query='{query}'...")
    macro_headlines = _fetch_news(query)
    logger.info(f"Got {len(macro_headlines)} macro headlines")
    
    logger.info("Running FinBERT scoring...")
    crypto_score, crypto_scored = _score_headlines(crypto_headlines)
    macro_score, macro_scored   = _score_headlines(macro_headlines)

    combined_score = round(crypto_score * 0.6 + macro_score * 0.4, 3)

    if combined_score > 0.1:
        signal = "bullish"
    elif combined_score < -0.1:
        signal = "bearish"
    else:
        signal = "neutral"

    logger.info(f"RESULT signal={signal}, combined={combined_score}, crypto={crypto_score}, macro={macro_score}")

    return {
        "crypto_headlines"  : crypto_headlines,
        "macro_headlines"   : macro_headlines,
        "crypto_score"      : crypto_score,
        "macro_score"       : macro_score,
        "combined_score"    : combined_score,
        "signal"            : signal,
        "crypto_scored"     : crypto_scored,
        "macro_scored"      : macro_scored
    }

def _fetch_coin_desk_rss(coin_id: str, limit: int = 5) -> list[str]:
    """Fetch crypto headlines from CoinDesk RSS — free, no API key needed."""
    url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    root = ET.fromstring(response.content)
    headlines = []
    for item in root.findall(".//item"):
        title = item.findtext("title")
        if title:
            headlines.append(title.strip())
        if len(headlines) >= limit:
            break

    logger.info(f"CoinDesk RSS returned {len(headlines)} headlines")
    return headlines

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