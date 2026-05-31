import json
import requests

from src.agents.tools.state import TradingDecisionState
from src.core.config import get_ollama_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

_settings = get_ollama_settings()

def decision_report_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state["symbol"]

    logger.info(f"START symbol={symbol} - building prompt...")

    strategy = state.get("strategy", {}) # the original proposal
    critic   = state.get("critic", {})   # potential challenges

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
        raise ValueError(f"Decision report node received non-JSON response: {exc}") from exc
    
    final_action = result.get("final_action", "WAIT")
    confidence   = result.get("confidence", 0.0)

    logger.info(f"RESULT final_action={final_action} confidence={confidence} critic_verdict={critic.get('verdict')}")

    return {"decision_report": {
        "final_action": final_action,
        "confidence":   confidence,
        "entry_zone":   result.get("entry_zone"),
        "bull_case":    result.get("bull_case", ""),
        "bear_case":    result.get("bear_case", ""),
        "final_thesis": result.get("final_thesis", ""),
        "key_risks":    result.get("key_risks", ""),
    }}

def _build_prompt(state: TradingDecisionState) -> str:    
    symbol = state["symbol"]
    strategy = state.get("strategy", {})
    critic   = state.get("critic", {})

    prompt = f"""You are a senior trading analyst making the final decision.
    You have received a strategy proposal and a critic's review. Weigh both sides and produce the final report.
    If the critic's severity is high or verdict is reject, lower the confidence or change the action.

    SYMBOL: {symbol}

    STRATEGY PROPOSAL:
    - Action: {strategy.get("action")}
    - Confidence: {strategy.get("confidence")}
    - Thesis: {strategy.get("thesis")}
    - Stated risks: {strategy.get("risks")}

    CRITIC REVIEW:
    - Verdict: {critic.get("verdict")}
    - Severity: {critic.get("severity")}
    - Challenges: {critic.get("challenges")}
    - Contradictions: {critic.get("contradictions")}
    - Risk flags: {critic.get("risk_flags")}

    Respond ONLY with valid JSON — no extra text, no markdown:
    {{
        "final_action": "BUY" or "WAIT" or "AVOID",
        "confidence": 0.0 to 1.0,
        "entry_zone": "price range or null if not BUY",
        "bull_case": "one sentence best case",
        "bear_case": "one sentence worst case",
        "final_thesis": "2-3 sentence final reasoning",
        "key_risks": "most important risks to watch"
    }}"""

    return prompt