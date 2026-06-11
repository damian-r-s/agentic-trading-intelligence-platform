# Documentation

Architecture decisions, data flows, and design notes for the Agentic Trading Intelligence Platform.

## Data Flow

```
Binance REST API (read-only)
  │
  ├── BinanceClient              Raw HTTP, signed + public endpoints
  │     ├── get_account_info()
  │     ├── get_my_trades(symbol)
  │     ├── get_open_orders()
  │     ├── get_klines(symbol, interval, limit)
  │     ├── get_order_book(symbol, limit)
  │     ├── get_24h_ticker(symbol)
  │     ├── get_ticker_prices(symbols)
  │     ├── get_trade_fee(symbol)
  │     └── get_exchange_info()
  │
  ├── BinancePortfolioService    Normalised portfolio state
  │     ├── get_portfolio_snapshot()
  │     └── get_agent_portfolio_state()
  │           └── includes current_prices (USDT conversion via ticker)
  │
  └── BinanceMarketDataService   Normalised market data
        ├── get_klines()          → list of OHLCV dicts
        ├── get_order_book()      → bids/asks + spread + depth
        └── get_24h_stats()       → price change, volume, high/low
```

## Provider Interfaces (`src/market_data/providers.py`)

Agents depend on Protocol interfaces, not concrete classes. This allows swapping data sources without touching agent code.

| Interface | Used By | Implementation |
|---|---|---|
| `CandleProvider` | technical_analysis_node, momentum_node | `BinanceMarketDataService` |
| `OrderBookProvider` | liquidity_node | `BinanceMarketDataService` |
| `TickerProvider` | momentum_node, market_regime_node | `BinanceMarketDataService` |

## LangGraph Agent State (`src/agents/tools/state.py`)

```python
class TradingDecisionState(TypedDict, total=False):
    # Input
    symbol: str

    # portfolio_snapshot_node — runs first, all parallel nodes read its output
    portfolio: dict          # balances, prices, open orders, trade history
    daily_candles: list      # 250 daily OHLCV candles, shared by regime + momentum nodes

    # Parallel nodes (fan-out) — each writes to its own field independently
    risk_metrics: dict       # HHI, concentration, locked funds, unrealized/realized P&L
    technical_analysis: dict # EMA, RSI, MACD, Bollinger Bands, ATR, OBV + signals
    market_regime: dict      # bull/bear/sideways, trend strength, SMA cross, volatility
    momentum: dict           # RSI/MACD/OBV/BB signals, price acceleration
    liquidity: dict          # spread %, depth bias, bid/ask imbalance
    correlation: dict        # BTC/ETH correlation coefficients, diversification score
    news_sentiment: dict     # FinBERT scores, crypto/macro headlines, combined signal

    # Sequential nodes (fan-in)
    strategy: dict           # action: BUY/WAIT/AVOID, confidence, entry_zone, thesis, risks
    critic: dict             # challenges, risk_flags, contradictions, severity, verdict
    decision_report: dict    # final_action, confidence, entry_price, stop_loss, take_profit,
                             # breakeven_price, fee_rate_pct, total_fees_usdt,
                             # risk_reward_ratio, position_size_pct, position_size_usdt,
                             # binance_orders (step_1_entry LIMIT + step_2_oco_after_fill OCO),
                             # invalidation, bull_case, bear_case, final_thesis, key_risks
```

## Graph Execution Order

```
START
  └── portfolio_snapshot_node
        └── [parallel fan-out — all nodes below run concurrently]
              ├── risk_metrics_node
              ├── technical_analysis_node
              ├── market_regime_node
              ├── momentum_node
              ├── liquidity_node
              ├── correlation_node
              └── news_sentiment_node
                    └── [fan-in — strategy waits for all parallel nodes]
                          └── strategy_node  (Ollama LLM)
                                └── critic_node  (Ollama LLM)
                                      └── decision_report_node  (Ollama LLM)
                                            └── END
```

Parallel nodes all read from the same shared state and write to separate fields.
LangGraph merges their outputs automatically before passing state to the next sequential node.

## Risk Metrics Design (`src/agents/tools/risk.py`)

**Position sizing** uses current prices fetched via `/api/v3/ticker/price` at portfolio snapshot time. All values are converted to USDT using a two-pass price resolution:

1. Stablecoins → price = 1.0
2. Assets with direct USDT pairs → price from ticker
3. Assets quoted in non-USDT (e.g. BTCETH) → price × quote_price_in_USDT

**P&L calculation** uses the weighted average cost basis (WAVG) method:
- Each BUY trade increases the cost basis pool.
- Each SELL trade computes realised P&L against the current average, then reduces the pool proportionally.
- Quote assets are converted to USDT using current prices (approximation — historical rates are not stored).

**HHI (Herfindahl-Hirschman Index)** measures portfolio concentration:
- `HHI = Σ (weight_i)²` where weight is each asset's share of total portfolio value
- Range: 0.0 (perfectly diversified) → 1.0 (single asset)
- HHI > 0.25 is generally considered high concentration

## News & Sentiment Node (`src/agents/tools/nodes/news_sentiment.py`)

Two headline sources are combined:

| Source | Scope | Weight |
|---|---|---|
| CoinDesk RSS | Crypto-specific headlines (free, no key) | 60% |
| NewsAPI | Broader macro + crypto query (API key required) | 40% |

Headlines are scored by **FinBERT** (`ProsusAI/finbert`) which classifies each headline as positive / negative / neutral with a probability score. The sentiment signal is:

```
sentiment_score = positive_prob - negative_prob   (per headline)
combined_score  = mean(crypto_scores) * 0.6 + mean(macro_scores) * 0.4

signal = "bullish"  if combined_score >  0.1
         "bearish"  if combined_score < -0.1
         "neutral"  otherwise
```

FinBERT is loaded once at module import time. First run downloads ~420MB of model weights to `~/.cache/huggingface/`.

## Portfolio Intelligence Graph (planned — Step 1.7)

A second LangGraph graph running daily on a separate schedule. Independent from the 4h trading signal pipeline.

```
START
  └── data_aggregation_node   — parallel fetch: CoinGecko, GitHub, DeFiLlama, FRED, Reddit
        └── asset_screener_node       — score top-100 assets, rank by safety composite score
              └── portfolio_optimizer_node  — compare current holdings vs screener shortlist
                    └── rebalancing_engine_node   — compute fee-aware trades to reach target
                          └── recommendation_report_node  — LLM final report
                                └── END
```

**Safety score weights:** market cap rank 20% · liquidity 15% · volatility 15% · developer activity 15% · sentiment 10% · Fear & Greed 10% · portfolio correlation 10% · TVL 5%

**Rebalancing constraints:** minimum 100 USDT per trade · 0.1% fee deducted · locked funds excluded · generates LIMIT order parameters per trade

---

## Governance & Control Plane (planned — Step 1.10)

A deterministic, non-LLM layer that wraps every LLM-driven proposal (`decision_report`, and later `recommendation_report`) before it reaches a human or the exchange. Full rationale and detail in [docs/ROADMAP.md](ROADMAP.md) — Step 1.10. Summary of the data flow:

```
decision_report_node (LLM)
  └── risk_gate_node       — hard limit checks against src/agents/tools/risk.py
        │                     (max position size, total exposure, post-trade HHI,
        │                      drawdown circuit breaker, volatility halt)
        │                     → { risk_check: PASS|WARN|BLOCK, violations[] }
        └── policy_engine_node — versioned rules from `policies` table
              │                   → routing: AUTO_APPROVE | NEEDS_APPROVAL | BLOCKED
              └── audit_log_node — append-only: state snapshot, LLM prompts +
                                    raw responses, risk_check, policy_result
                                    → `audit_log` table
```

**Proposal state machine** (`proposals` table) — created for every run routed `AUTO_APPROVE` or `NEEDS_APPROVAL` (a `BLOCKED` routing ends the run, logged but with no proposal):

```
PENDING_APPROVAL ──approve──► APPROVED
                 └─reject───► REJECTED
(TTL exceeded)   ──────────► EXPIRED
```

`AUTO_APPROVE` proposals are inserted directly as `APPROVED` — still visible in `/approvals` and fully audited. `AUTO_APPROVE` policies are opt-in and start disabled.

**Policy rule format** (`policies` table, `rule_type` + JSONB `params`):

```json
{ "rule_type": "symbol_denylist", "params": { "symbols": ["LUNAUSDT", "FTTUSDT"] } }
{ "rule_type": "trading_hours", "params": { "blackout_utc": [["00:00", "00:30"]] } }
{ "rule_type": "max_trades_per_day", "params": { "limit": 3 } }
{ "rule_type": "max_concurrent_positions", "params": { "limit": 5 } }
{ "rule_type": "min_confidence_auto_approve", "params": { "min_confidence": 0.85, "max_critic_severity": "low" } }
```

**Reconciliation (Execution Layer — advisory only, no order placement):** the Binance API key stays read-only. An hourly `reconciliation-worker` CronJob calls `get_my_trades()` and matches fills to `APPROVED` proposals by symbol + time window (since `approved_at`) + price proximity to `entry_price`, writing a row to `executions` with `MATCHED` or `UNMATCHED`. `UNMATCHED` fills (manual trades outside the approval flow) are flagged for audit and trigger a Grafana alert.

---

## Monitoring & Observability (planned — Step 1.10)

Adds Prometheus + Alertmanager alongside the Grafana pod already planned in Step 1.6, so Grafana serves both signal-quality dashboards (Postgres datasource) and system/governance dashboards (Prometheus datasource).

**Prometheus metrics** (via `prometheus-fastapi-instrumentator` + custom):

| Metric | Purpose |
|---|---|
| `agent_pipeline_duration_seconds{symbol, node}` | Per-node timing across the LangGraph pipeline |
| `llm_call_duration_seconds{node}` | Ollama call latency per node |
| `llm_call_errors_total{node, error_type}` | LLM call failures, including JSON-parse errors |
| `risk_engine_violations_total{violation_type}` | Risk gate violations by type |
| `policy_engine_decisions_total{routing}` | Count of AUTO_APPROVE / NEEDS_APPROVAL / BLOCKED |
| `approval_queue_depth` | Current pending-approval count |
| `approval_latency_seconds` | Time from proposal creation to approve/reject |
| `reconciliation_match_rate` | % of executions matched to an approved proposal |

**Grafana dashboards:** System Health, LLM Observability, Risk & Policy, Approval & Execution, and (Step 1.6) Signal Quality.

**Alertmanager → Telegram:** risk circuit breaker triggered, policy `BLOCKED` rate spike, LLM error rate above threshold, approval queue stale, reconciliation `UNMATCHED` execution.

---

## LLM Integration (`src/agents/tools/nodes/strategy.py`)

The strategy node calls a local **Ollama** instance via HTTP. The model and base URL are configurable via environment variables:

```
OLLAMA_BASE_URL=http://localhost:11434   (default)
OLLAMA_MODEL=llama3.2:3b               (default)
```

The prompt is structured JSON — Ollama's `format: "json"` flag forces valid JSON output. Temperature is set to 0.2 for consistent, low-variance decisions.

## Database (`src/core/databases/`)

PostgreSQL 16 with schema managed by **yoyo-migrations**. Migrations run automatically via a dedicated `migrate` container in `docker-compose.yml`.

| Migration | Tables |
|---|---|
| `001_cache_tables.sql` | Generic cache key-value store |
| `002_market_data.sql` | OHLCV candles, order book snapshots |
| `003_analysis.sql` | Agent analysis results |
| `004_news.sql` | News headlines and sentiment scores |
| `005_ml_models.sql` | ML model artefacts and metadata |
| `006_backtesting.sql` | Backtest runs and results |
| `007_portfolio.sql` | Portfolio snapshots and trade history |

## Binance API Notes

- All portfolio endpoints use **signed requests** (HMAC-SHA256).
- Market data endpoints (klines, order book, ticker) are **public** — no signature required.
- `recv_window` defaults to 5000ms; increase if you see timestamp errors.
- Rate limits: 1200 request weight per minute. `get_exchange_info()` costs 20 weight; most others cost 1–5.
- Create a **read-only** API key with `USER_DATA` access. Keep trading and withdrawals **disabled**.
