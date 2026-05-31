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
    decision_report: dict    # final_action, confidence, bull_case, bear_case, key_risks, final_thesis
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
