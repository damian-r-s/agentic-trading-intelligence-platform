# Agentic Trading Intelligence Platform

Production-grade multi-agent AI trading research platform. The system prepares trading decisions for human approval — it does not trade autonomously.

Powered by LangGraph, FastAPI, Ollama, and the Binance API.

## Architecture

```
FastAPI
  └── LangGraph Orchestrator
        ├── Portfolio Snapshot Node  — balances, prices, open orders, daily candles
        │     [runs first — all parallel nodes read from its output]
        │
        ├── [parallel fan-out]
        │     ├── Risk Metrics Node       — HHI, concentration, locked funds, P&L
        │     ├── Technical Analysis Node — RSI, MACD, EMA, Bollinger Bands, ATR, OBV
        │     ├── Market Regime Node      — bull/bear/sideways, SMA cross, volatility
        │     ├── Momentum Node           — price acceleration, volume spikes, OBV trend
        │     ├── Liquidity Node          — order book, spread, depth bias, slippage
        │     ├── Correlation Node        — BTC/ETH correlation, diversification score
        │     └── News & Sentiment Node   — CoinDesk RSS + NewsAPI, FinBERT scoring
        │
        ├── Strategy Node        — BUY / WAIT / AVOID + entry zone + thesis (Ollama LLM)
        ├── Critic Node          — challenges the proposal, flags contradictions, rates severity
        └── Decision Report Node — final report weighing strategy vs critic, adjusted confidence
              └── Human Approval  ← YOU decide
```

## Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- LangGraph + LangChain
- Ollama (local LLM — llama3.2:3b by default)
- FinBERT via HuggingFace `transformers` (news sentiment)
- Binance REST API (read-only)
- PostgreSQL 16 + yoyo migrations
- Docker + Docker Compose

## Project Structure

```
.
├── app.py                        # FastAPI app + router registration
├── main.py                       # Uvicorn entrypoint
├── docker-compose.yml            # postgres + migrate + api services
├── DockerFile
├── src/
│   ├── api/
│   │   ├── portfolio.py          # GET /portfolio, /portfolio/state, /trade-fees
│   │   ├── market_data.py        # GET /market-data/{symbol}/candles|order-book|stats|indicators
│   │   ├── analyze.py            # GET /agent/analyze
│   │   ├── query.py              # RAG query endpoint
│   │   └── ingestion.py          # PDF ingestion endpoint
│   ├── agents/
│   │   └── tools/
│   │       ├── graph.py          # LangGraph workflow definition
│   │       ├── state.py          # TradingDecisionState (shared agent state)
│   │       ├── indicators.py     # EMA, SMA, RSI, MACD, Bollinger, ATR, OBV
│   │       ├── risk.py           # HHI, VaR, Kelly, P&L calculations
│   │       └── nodes/            # Individual graph nodes
│   │             ├── portfolio_snapshot.py
│   │             ├── risk_metrics.py
│   │             ├── technical_analysis.py
│   │             ├── market_regime.py
│   │             ├── momentum.py
│   │             ├── liquidity.py
│   │             ├── correlation.py
│   │             ├── news_sentiment.py
│   │             ├── strategy.py
│   │             ├── critic.py
│   │             └── decision_report.py
│   ├── exchanges/
│   │   └── binance/
│   │       ├── client.py         # Raw Binance HTTP client (signed + public)
│   │       ├── service.py        # Portfolio normalisation service
│   │       └── market_data.py    # OHLCV, order book, 24h stats
│   ├── market_data/
│   │   └── providers.py          # Protocol interfaces for data providers
│   ├── core/
│   │   ├── config.py             # Settings (env vars, dataclasses)
│   │   ├── logging.py            # Structured logger
│   │   ├── cache.py              # DB-backed cache layer
│   │   ├── store.py              # Vector store access
│   │   └── databases/
│   │         ├── database.py     # Async DB connection
│   │         ├── migrations/     # yoyo SQL migrations (001–007)
│   │         └── repositories/   # Data access objects per domain
│   ├── retrieval/                # FAISS vector store + embeddings
│   ├── ingestion/                # PDF loader + chunking
│   └── ui/                       # Static frontend (HTML/CSS/JS)
└── test/
```

## Run Locally

Requires Ollama running locally with at least one model pulled:

```bash
ollama pull llama3.2:3b
```

Then start the stack:

```bash
docker compose up
```

Or run the API directly (needs Postgres already running):

```bash
uvicorn app:app --reload
```

## Environment Variables

Copy `.env.example` to `.env`:

```bash
# Binance (read-only key — disable trading and withdrawals)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_BASE_URL=https://api.binance.com
BINANCE_RECV_WINDOW=5000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# News
NEWS_API_KEY=your_newsapi_key

# FinBERT
FINBERT_MODEL=ProsusAI/finbert

# Postgres
POSTGRES_HOST=localhost
```

## API Endpoints

### Portfolio

```
GET /portfolio                     Spot account balances snapshot
GET /portfolio/state               Balances + trade history + open orders + risk metrics
GET /trade-fees                    Maker/taker fees for all held symbols
GET /trade-fees?symbol=BTCUSDT     Fees for a specific symbol
```

### Market Data

```
GET /market-data/{symbol}/candles?interval=4h&limit=200    OHLCV candles
GET /market-data/{symbol}/order-book?depth=20              Bid/ask book with spread and depth
GET /market-data/{symbol}/stats                            24h price change, volume, high/low
GET /market-data/{symbol}/indicators?interval=4h&limit=500 Technical indicators + signals
```

### Agent Workflow

```
GET /agent/analyze?symbol=BTCUSDT  Run full multi-agent analysis (default: BTCUSDT)
```

### RAG / Knowledge Base

```
POST /ingest                       Ingest a PDF into the vector store
POST /query                        Query the knowledge base with natural language
```

## Risk Metrics

Computed automatically in `/portfolio/state` and by the risk_metrics node in the agent pipeline.

| Metric | Description |
|---|---|
| `total_portfolio_value_usdt` | Total portfolio value in USDT |
| `position_values_usdt` | Per-asset value in USDT |
| `concentration_pct` | Percentage allocation per asset |
| `hhi` | Herfindahl-Hirschman Index (0 = diversified, 1 = single position) |
| `largest_position_by_value` | Biggest position by USDT value |
| `locked_value_usdt` / `locked_ratio` | Funds locked in open orders |
| `open_buy_orders_value_usdt` | Capital at risk in pending buy orders |
| `unrealized_pnl_by_asset` | Unrealized P&L vs average cost basis |
| `realized_pnl_by_asset` | Realized P&L from closed trades (WAVG method) |

## Implementation Milestones

- [x] Milestone 1 — Portfolio baseline: Binance client, portfolio state, risk metrics
- [x] Milestone 2 — Market data: OHLCV candles, order book, 24h stats, provider interfaces
- [x] Milestone 3 — Technical indicators: EMA/SMA, RSI, MACD, ATR, Bollinger Bands, OBV
- [x] Milestone 4 — LangGraph workflow: parallel agents, TradingDecisionState
- [x] Milestone 5 — News & Sentiment (FinBERT + CoinDesk RSS + NewsAPI) + Correlation node
- [x] Milestone 6 — PostgreSQL cache: yoyo migrations, repository layer, DB-backed cache
- [x] Milestone 7 — Complete agent pipeline: Critic node + Decision Report node
- [ ] Milestone 8 — ML regime detection: Hidden Markov Model replacing rule-based market regime node
- [ ] Milestone 9 — Kubernetes deployment: separate pods for API, FinBERT, Ollama, Postgres
- [ ] Milestone 10 — C++ engine: indicator + risk calculator via pybind11, ONNX inference bridge
- [ ] Milestone 11 — Price forecasting: LSTM / Temporal Fusion Transformer signal (PyTorch)
- [ ] Milestone 12 — Backtesting: walk-forward validation, signal attribution per agent
- [ ] Milestone 13 — RL execution agent: learned position sizing (PPO/SAC, stable-baselines3)

See [docs/ROADMAP.md](docs/ROADMAP.md) for full context, rationale, and implementation details.
