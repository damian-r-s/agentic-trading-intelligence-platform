import requests

from src.agents.tools.state import TradingDecisionState
from src.core.config import get_finbert_service_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

_finbert_url = get_finbert_service_settings().url

def sentiment_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state["symbol"]
    coin   = symbol.replace("USDT", "").lower()    
    logger.info(f"START symbol={symbol} coin={coin}")

    response = requests.get(f"{_finbert_url}/score", params={"symbol": symbol, "coin": coin}, timeout=30)
    response.raise_for_status()
    data = response.json()

    logger.info(f"RESULT signal={data['signal']} combined={data['combined_score']}")
    return {"news_sentiment": data}