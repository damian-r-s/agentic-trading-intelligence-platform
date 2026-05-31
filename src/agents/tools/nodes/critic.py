import json
import requests
from src.agents.tools.state import TradingDecisionState
from src.core.config import get_ollama_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

_settings = get_ollama_settings()

def critic_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state["symbol"]

    logger.info(f"START symbol={symbol} - building prompt...")

    prompt = _build_prompt(state)

    url = f"{_settings.base_url}/api/generate"
    logger.info(f"Calling Ollama model={_settings.model} at {url}...")

    resp = requests.post(
        url,
        json={
            "model": _settings.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,          
            "options": {"temperature": 0.2},  
        },
        timeout=120
    )
    resp.raise_for_status()

    raw = resp.json().get("response", "")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"Ollama returned invalid JSON: {raw!r}")    
        raise ValueError(f"Critic node received non-JSON response: {exc}") from exc

    severity = result.get("severity", "medium")
    verdict  = result.get("verdict", "caution")
    logger.info(f"RESULT severity={severity} verdict={verdict}")

    return {
        "critic": {
            "challenges":       result.get("challenges", []),
            "risk_flags":       result.get("risk_flags", []),
            "contradictions":   result.get("contradictions", []),
            "severity":         severity,
            "verdict":          verdict
        }        
    }

def _build_prompt(state: TradingDecisionState) -> str:
    strategy = state.get("strategy", {})
    tech     = state.get("technical_analysis", {})
    signals  = tech.get("signals", {})
    latest   = tech.get("latest", {})
    regime   = state.get("market_regime", {})
    mom      = state.get("momentum", {})
    news     = state.get("news_sentiment", {})
    corr     = state.get("correlation", {})
    liq      = state.get("liquidity", {})

    prompt = f"""You are a risk-focused trading critic. The strategy agent has proposed a decision.
    Your job is to challenge it. Look for contradictions between signals, risks being ignored,
    and reasons the proposed action could be wrong.

    SYMBOL: {state.get("symbol")}

    STRATEGY PROPOSAL:
    - Action: {strategy.get("action")}
    - Confidence: {strategy.get("confidence")}
    - Thesis: {strategy.get("thesis")}
    - Stated risks: {strategy.get("risks")}

    SIGNALS TO SCRUTINISE:
    - RSI: {latest.get("rsi_14")} [{signals.get("rsi_zone")}]
    - Trend: {signals.get("trend")} | MACD: {signals.get("macd_cross")}
    - Regime: {regime.get("regime")} | Strength: {regime.get("trend_strength")}
    - Volatility: {regime.get("volatility")}
    - OBV trend: {mom.get("obv_trend")}
    - Sentiment: {news.get("signal")} (score: {news.get("combined_score")})
    - BTC correlation: {corr.get("btc_correlation_label")}
    - Spread: {liq.get("spread_pct")}% | Depth bias: {liq.get("depth_bias")}

    Respond ONLY with valid JSON — no extra text, no markdown:
    {{
        "challenges": ["specific challenge 1", "specific challenge 2"],
        "risk_flags": ["risk 1", "risk 2"],
        "contradictions": ["signal A says X but signal B says Y"],
        "severity": "low" or "medium" or "high",
        "verdict": "agree" or "caution" or "reject"
    }}"""

    return prompt