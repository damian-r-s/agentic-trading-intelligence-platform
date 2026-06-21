import json
import requests

from src.agents.tools.state import TradingDecisionState
from src.core.config import get_ollama_settings
from src.core.logging import get_logger

from src.core.databases.repositories.analysis_repo import (
    create_analysis_run,
    insert_trading_decision,
    complete_analysis_run,
)

logger = get_logger(__name__)

_settings = get_ollama_settings()

# Risk per trade as a fraction of total portfolio value (1% fixed fractional)
_PORTFOLIO_RISK_FRACTION = 0.01
_MAX_POSITION_SIZE_PCT   = 10.0
_MIN_POSITION_SIZE_USDT  = 100.0
# Stop-limit price is placed slightly below the stop to ensure fill
_STOP_LIMIT_SLIPPAGE     = 0.995
# Binance spot fee: 0.1% standard, 0.075% with BNB — change here if using BNB discount
_FEE_RATE = 0.001


def _compute_trade_parameters(
    final_action: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    portfolio_value_usdt: float,
) -> dict:
    """Compute fee-adjusted position size and Binance order parameters from LLM prices."""

    empty = {
        "fee_rate_pct":      None,
        "breakeven_price":   None,
        "risk_reward_ratio": None,
        "position_size_pct": None,
        "position_size_usdt": None,
        "binance_orders":    None,
    }

    if final_action != "BUY" or entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
        return empty

    # Fee-adjusted prices — what you actually pay/receive after Binance fees
    effective_entry  = entry_price  * (1 + _FEE_RATE)
    effective_tp     = take_profit  * (1 - _FEE_RATE)
    effective_sl     = stop_loss    * (1 - _FEE_RATE)
    breakeven_price  = round(entry_price * (1 + 2 * _FEE_RATE), 2)

    risk_per_unit = effective_entry - effective_sl
    if risk_per_unit <= 0:
        return empty

    reward_per_unit   = effective_tp - effective_entry
    risk_reward_ratio = round(reward_per_unit / risk_per_unit, 2)

    # Fixed fractional: risk exactly 1% of portfolio on this trade (using fee-adjusted risk)
    risk_budget_usdt   = portfolio_value_usdt * _PORTFOLIO_RISK_FRACTION
    position_size_usdt = risk_budget_usdt / (risk_per_unit / effective_entry)
    position_size_usdt = max(position_size_usdt, _MIN_POSITION_SIZE_USDT)
    position_size_pct  = min(
        round(position_size_usdt / portfolio_value_usdt * 100, 2),
        _MAX_POSITION_SIZE_PCT,
    )
    position_size_usdt = round(portfolio_value_usdt * position_size_pct / 100, 2)

    fee_usdt_entry  = round(position_size_usdt * _FEE_RATE, 4)
    fee_usdt_exit   = round(position_size_usdt * _FEE_RATE, 4)
    total_fees_usdt = round(fee_usdt_entry + fee_usdt_exit, 4)

    stop_limit_price = round(stop_loss * _STOP_LIMIT_SLIPPAGE, 2)

    binance_orders = {
        "step_1_entry": {
            "order_type":    "LIMIT",
            "side":          "BUY",
            "price":         entry_price,
            "amount_usdt":   position_size_usdt,
            "fee_usdt":      fee_usdt_entry,
            "time_in_force": "GTC",
            "instruction": (
                f"Place a LIMIT BUY order at {entry_price}. "
                f"Spend {position_size_usdt} USDT ({position_size_pct}% of portfolio). "
                f"Binance fee: ~{fee_usdt_entry} USDT. "
                f"Break-even price (covers both fees): {breakeven_price}. "
                "Use GTC (Good Till Cancelled)."
            ),
        },
        "step_2_oco_after_fill": {
            "order_type":        "OCO",
            "side":              "SELL",
            "take_profit_price": take_profit,
            "stop_price":        stop_loss,
            "stop_limit_price":  stop_limit_price,
            "fee_usdt":          fee_usdt_exit,
            "instruction": (
                f"After the buy fills, immediately place an OCO SELL order. "
                f"Take profit at {take_profit} (net after fee: ~{round(effective_tp, 2)}). "
                f"Stop at {stop_loss} (limit at {stop_limit_price}, net after fee: ~{round(effective_sl, 2)}). "
                f"Total round-trip fees: ~{total_fees_usdt} USDT. "
                "Whichever triggers first automatically cancels the other."
            ),
        },
    }

    return {
        "fee_rate_pct":       round(_FEE_RATE * 100, 3),
        "breakeven_price":    breakeven_price,
        "risk_reward_ratio":  risk_reward_ratio,
        "position_size_pct":  position_size_pct,
        "position_size_usdt": position_size_usdt,
        "total_fees_usdt":    total_fees_usdt,
        "binance_orders":     binance_orders,
    }

def _persist_decision(
    symbol: str,
    final_action: str,
    confidence: float,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    thesis: str,
    risks: str,
    price_at_signal: float | None,
) -> None:
    """Persist the decision for later evaluation. Never raises — logs and swallows DB errors."""
    try:
        run_id = create_analysis_run(symbol=symbol)
        insert_trading_decision(
            run_id=run_id,
            action=final_action,
            confidence=confidence,
            entry_zone={
                "entry_price": entry_price or None,
                "stop_loss": stop_loss or None,
                "take_profit": take_profit or None,
            },
            thesis=thesis,
            risks=risks,
            price_at_signal=price_at_signal,
        )
        complete_analysis_run(run_id, "done")
    except Exception as exc:
        logger.error(f"failed to persist trading decision: {exc}")


def decision_report_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol   = state["symbol"]
    strategy = state.get("strategy", {})
    critic   = state.get("critic", {})

    logger.info(f"START symbol={symbol} — building prompt...")

    prompt = _build_prompt(state)

    url = f"{_settings.base_url}/api/generate"
    logger.info(f"Calling Ollama model={_settings.model} at {url}...")
    resp = requests.post(
        url,
        json={
            "model":   _settings.model,
            "prompt":  prompt,
            "format":  "json",
            "stream":  False,
            "options": {"temperature": 0.2},
        },
        timeout=180,
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
    entry_price  = float(result.get("entry_price") or 0)
    stop_loss    = float(result.get("stop_loss")   or 0)
    take_profit  = float(result.get("take_profit") or 0)

    # Portfolio value from risk metrics for position sizing
    risk_metrics         = state.get("risk_metrics", {})
    portfolio_value_usdt = float(risk_metrics.get("total_portfolio_value_usdt") or 0)

    trade_params = _compute_trade_parameters(
        final_action, entry_price, stop_loss, take_profit, portfolio_value_usdt
    )

    logger.info(
        f"RESULT final_action={final_action} confidence={confidence} "
        f"critic_verdict={critic.get('verdict')} "
        f"rr={trade_params['risk_reward_ratio']} "
        f"position_size={trade_params['position_size_pct']}% "
        f"breakeven={trade_params['breakeven_price']} "
        f"fees={trade_params.get('total_fees_usdt')} USDT"
    )
    
    price_at_signal = state.get("technical_analysis", {}).get("latest", {}).get("close")
    _persist_decision(
        symbol, final_action, confidence, entry_price, stop_loss, take_profit,
        result.get("final_thesis", ""), result.get("key_risks", ""), price_at_signal,
    )

    return {"decision_report": {
        "final_action":       final_action,
        "confidence":         confidence,
        "entry_price":        entry_price or None,
        "stop_loss":          stop_loss   or None,
        "take_profit":        take_profit or None,
        "breakeven_price":    trade_params["breakeven_price"],
        "risk_reward_ratio":  trade_params["risk_reward_ratio"],
        "fee_rate_pct":       trade_params["fee_rate_pct"],
        "total_fees_usdt":    trade_params.get("total_fees_usdt"),
        "position_size_pct":  trade_params["position_size_pct"],
        "position_size_usdt": trade_params["position_size_usdt"],
        "binance_orders":     trade_params["binance_orders"],
        "invalidation":       result.get("invalidation", ""),
        "bull_case":          result.get("bull_case", ""),
        "bear_case":          result.get("bear_case", ""),
        "final_thesis":       result.get("final_thesis", ""),
        "key_risks":          result.get("key_risks", ""),
    }}

def _build_prompt(state: TradingDecisionState) -> str:
    symbol   = state["symbol"]
    strategy = state.get("strategy", {})
    critic   = state.get("critic", {})
    tech     = state.get("technical_analysis", {})
    latest   = tech.get("latest", {})

    current_price = latest.get("close", "unknown")
    atr           = latest.get("atr_14", "unknown")
    bb_upper      = latest.get("bb_upper", "unknown")
    bb_lower      = latest.get("bb_lower", "unknown")

    return f"""You are a senior trading analyst making the final decision.
Weigh the strategy proposal against the critic's review and produce the final report.
If the critic's severity is high or verdict is reject, lower confidence or change the action.

SYMBOL: {symbol}
CURRENT PRICE: {current_price}
ATR(14): {atr}  — use this to gauge volatility when setting stop loss and take profit
BOLLINGER UPPER: {bb_upper} | LOWER: {bb_lower}

STRATEGY PROPOSAL:
- Action: {strategy.get("action")}
- Confidence: {strategy.get("confidence")}
- Entry zone: {strategy.get("entry_zone")}
- Thesis: {strategy.get("thesis")}
- Stated risks: {strategy.get("risks")}

CRITIC REVIEW:
- Verdict: {critic.get("verdict")}
- Severity: {critic.get("severity")}
- Challenges: {critic.get("challenges")}
- Contradictions: {critic.get("contradictions")}
- Risk flags: {critic.get("risk_flags")}

TRADE PARAMETER RULES (follow these exactly):
- entry_price: specific number. For BUY use lower end of entry zone. For WAIT/AVOID use null.
- stop_loss: For BUY set below nearest support or 2× ATR below entry. For WAIT/AVOID use null.
- take_profit: For BUY set at nearest resistance or Bollinger upper band. For WAIT/AVOID use null.
- invalidation: one sentence — what market condition would prove this thesis wrong.

Respond ONLY with valid JSON — no extra text, no markdown:
{{
    "final_action": "BUY" or "WAIT" or "AVOID",
    "confidence": 0.0 to 1.0,
    "entry_price": number or null,
    "stop_loss": number or null,
    "take_profit": number or null,
    "invalidation": "condition that cancels this trade",
    "bull_case": "one sentence best case scenario",
    "bear_case": "one sentence worst case scenario",
    "final_thesis": "2-3 sentence final reasoning",
    "key_risks": "most important risks to watch"
}}"""
