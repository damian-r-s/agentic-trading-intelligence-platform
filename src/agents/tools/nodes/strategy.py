from typing import Any
import json
from openai import OpenAI

from src.agents.tools.state import TradingDecisionState
from src.core.config import get_openai_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

_settings = get_openai_settings()
_openai = OpenAI(api_key=_settings.api_key)

def _build_prompt(state: TradingDecisionState) -> str:
    tech = state.get("technical_analysis", {})
    regime = state.get("market_regime", {})
    mom = state.get("momentum", {})    
    liq = state.get("liquidity", {})
    corr = state.get("correlation", {})
    news = state.get("news_sentiment", {})
    risk = state.get("risk_metrics", {})

    latest = tech.get("latest", {})
    signals = tech.get("signals", {})

    return f"""You are professional crypto trading analyst. Based on the singnals below, produce a trading decision.

SYMBOL: {state.get("symbol")}

TECHNICAL ANALYSIS:
- Price: {latest.get("close")}
- RSI(14): {latest.get("rsi_14")} [{signals.get("rsi_zone")}]
- MACD: {signals.get("macd_cross")}
- Trend: {signals.get("trend")}
- Bollinger: {signals.get("bb_position")}

MARKET REGIME:
- Regime: {regime.get("regime")} | Strength: {regime.get("trend_strength")}
- Volatility: {regime.get("volatility")} | SMA cross: {regime.get("sma_cross")}

MOMENTUM:
- RSI signal: {mom.get("rsi_signal")} | MACD: {mom.get("macd_signal")}
- OBV trend: {mom.get("obv_trend")} | BB: {mom.get("bb_position")}

LIQUIDITY:
- Spread: {liq.get("spread_pct")}% | Depth imbalance: {liq.get("depth_imbalance")}
- Slippage estimate: {liq.get("slippage_estimate")}


CORRELATION:
- BTC correlation: {corr.get("btc_correlation")} [{corr.get("btc_correlation_label")}]
- ETH correlation: {corr.get("eth_correlation")} [{corr.get("eth_correlation_label")}]
- Diversification: {corr.get("diversification_benefit")}

NEWS & SENTIMENT:
- Signal: {news.get("signal")} | Combined score: {news.get("combined_score")}
- Crypto score: {news.get("crypto_score")} | Macro score: {news.get("macro_score")}

RISK:
- Asset count: {risk.get("asset_count")} | Open orders: {risk.get("open_order_count")}
- Locked funds: {risk.get("locked_asset_count")} assets


Respond ONLY with valid JSON in this exact format: 
{{
    "action": "BUY" or "WAIT" or "AVOID",
    "confidence": 0.0 to 1.0,
    "entry_zone": "price range or null if not BUY",
    "thesis": "2-3 sentence reasoning",
    "risk": "main risk factors"
}}"""

def strategy_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state.get("symbol")
    logger.info(f"START symbol={symbol} — building prompt...")

    prompt = _build_prompt(state)

    logger.info(f"Calling OpenAI model={_settings.model}...")
    response = _openai.chat.completions.create(
        model=_settings.model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    raw = response.choices[0].message.content
    decision = json.loads(raw)

    action     = decision.get("action", "WAIT")
    confidence = decision.get("confidence", 0.0)
    logger.info(f"RESULT action={action} confidence={confidence}")

    return {"strategy": {
        "action":     action,
        "confidence": confidence,
        "entry_zone": decision.get("entry_zone"),
        "thesis":     decision.get("thesis", ""),
        "risks":      decision.get("risk", ""),
    }}