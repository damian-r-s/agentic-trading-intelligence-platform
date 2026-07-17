# Agentic Trading Intelligence Platform

AI agents that automate financial research and generate actionable trading insights for traders and analysts.

Reduces research time from hours to minutes while maintaining full human control over execution.

This is not an automated trading bot — it is a decision intelligence system designed to augment human judgment.

## Problem

Financial research is time-consuming, fragmented, and noisy, requiring traders to manually combine multiple data sources and signals.

Traders and analysts must manually process:
- market data
- technical indicators
- news and sentiment
- portfolio risk

This leads to slow decisions, inconsistent outcomes, and cognitive overload.

## Example

**Input:**
BTCUSDT

**System:**
→ collects market data, technical indicators, and news
→ evaluates risk and portfolio exposure
→ generates a structured trade thesis

Output (decision report):
- Decision: BUY / WAIT / AVOID
- Entry zone
- Stop loss / Take profit
- Risk assessment
- Explanation

## Why Now

- LLMs enable reasoning over complex and unstructured financial data
- Multi-agent systems allow modular analysis pipelines
- Increasing demand for AI-assisted trading tools

## Target Users

- Retail traders looking to improve decision quality and reduce research time
- Crypto investors managing multi-asset portfolios  
- Quant-curious individuals without full infrastructure  

## Value Proposition

The platform reduces manual research and provides structured, explainable trade decisions.

Instead of spending hours combining indicators, news, and portfolio risk,
users receive a single coherent, explainable decision report with full transparency and human control.

Designed to be trusted: all decisions are explainable and remain under human control.

## Core Capabilities

- Multi-agent financial analysis pipeline  
- Portfolio-aware risk evaluation  
- News and sentiment integration  
- Explainable AI decision reports  
- Human-in-the-loop approval workflow  

## Architecture (for technical audience)

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
        └── Decision Report Node — final report: entry, SL, TP, breakeven, fees, Binance orders
              └── Governance & Control Plane (planned)  — deterministic guardrails on LLM output
                    ├── Risk Gate Node     — hard limit checks (exposure, HHI, drawdown, volatility)
                    ├── Policy Engine Node — routing: AUTO_APPROVE / NEEDS_APPROVAL / BLOCKED
                    └── Audit Log Node     — persists full run trace (prompts, responses, decisions)
                          └── Approval Engine — proposal queue (PENDING_APPROVAL → APPROVED/REJECTED)
                                └── Human Approval  ← YOU decide
                                      └── Execution Layer (advisory) — reconciles fills vs proposal

Portfolio Intelligence Graph (daily, separate pipeline)
  ├── Data Aggregation Node  — CoinGecko, GitHub, DeFiLlama, FRED, Reddit     [planned]
  ├── Asset Screener Node    — scores top-100 cryptos on safety metrics        [planned]
  ├── Portfolio Optimizer    — computes target allocation vs current holdings  [planned]
  ├── Rebalancing Engine     — exact trades to reach target (fee-aware)        [planned]
  └── Recommendation Report  — LLM-synthesised daily rebalancing report        [planned]
```

### Governance & Control Plane *(planned — see [docs/ROADMAP.md](docs/ROADMAP.md) Step 1.10)*

A deterministic, non-LLM layer between every LLM-driven proposal and the human/exchange:

- **Risk Engine** — hard limit checks (position size, exposure, HHI concentration, drawdown circuit breaker, volatility halt) independent of the LLM
- **Policy Engine** — versioned, DB-backed rules (symbol allow/deny lists, trading hours, confidence thresholds) that route each proposal to `AUTO_APPROVE`, `NEEDS_APPROVAL`, or `BLOCKED`
- **Audit Engine** — append-only log of every run: state snapshot, LLM prompts + raw responses, risk and policy results
- **Approval Engine** — tracked proposal state machine (`PENDING_APPROVAL → APPROVED/REJECTED/EXPIRED`) with an `/approvals` UI
- **Execution Layer** *(advisory + reconciliation only — Binance key stays read-only)* — matches manual fills to approved proposals and flags trades made outside the approval flow

## Tech Stack

**Backend**
- Python 3.12
- FastAPI + Uvicorn
- LangGraph + LangChain
- Ollama (local LLM — llama3.2:3b by default)
- FinBERT via HuggingFace `transformers` (news sentiment)
- Binance REST API (read-only)
- PostgreSQL 16 + yoyo migrations
- JWT authentication (python-jose + passlib) — multi-user, per-user encrypted Binance credentials (`cryptography` Fernet); users are admin-created via `scripts/create_user.py`, no self-registration
- Docker + Docker Compose

**Frontend** *(`frontend/` directory in this repo)*
- React 19 + TypeScript
- Tailwind CSS
- React Query (TanStack) — API fetching + caching
- React Router v6 — client-side routing + protected routes
- Zustand — auth + global state
- Recharts — portfolio and signal charts
- TradingView Lightweight Charts — candlestick + indicators

**Real-time & messaging** *(planned)*
- Apache Kafka (KRaft) — primary inter-service message bus: durable, replayable, exactly-once
- ZeroMQ — intra-pod only: C++ WebSocket feed handler → Kafka producer (<0.1ms)
- FastAPI WebSocket gateway — dedicated pod: Kafka consumer → browser live updates
- Avro + Schema Registry — typed message contracts across all Kafka topics

**Performance** *(planned)*
- C++20 via pybind11 — indicator engine (SIMD/AVX2), risk calculator, order book processor
- NumPy vectorisation — indicators.py before C++ rewrite
- Redis indicator cache — pre-computed results, skip recompute if candles unchanged
- Streaming algorithms — O(1) RSI/EMA/Bollinger update per tick (Welford's)

**Infrastructure**
- k3s (lightweight Kubernetes, self-hosted Linux VM) — manifests in `k8s/` for postgres, api, finbert, frontend, grafana, and the two workers as CronJobs; see [k8s/README.md](k8s/README.md). Written without a live cluster to test against — not yet verified on a real deployment.
- nginx — frontend pod (React build), proxies `/api/*` to the API service
- TLS ingress, Redis caching *(planned)*

**Monitoring & Observability**
- Grafana — Signal Quality dashboard (`grafana/dashboards/signal_quality.json`), reads directly from the Postgres `signal_metrics` table (IC / directional accuracy / simulated PnL, rolling 7/30/90-day windows)
- Prometheus `/metrics` scrape endpoint, Alertmanager alerts *(planned)*

## Project Structure

```
.
├── app.py                        # FastAPI app + router registration
├── main.py                       # Uvicorn entrypoint
├── docker-compose.yml            # postgres + migrate + api + finbert + evaluation-worker + metrics-engine + grafana
├── DockerFile
├── src/
│   ├── api/
│   │   ├── portfolio.py          # GET /portfolio, /portfolio/state, /trade-fees
│   │   ├── market_data.py        # GET /market-data/{symbol}/candles|order-book|stats|indicators
│   │   ├── analyze.py            # GET /agent/analyze
│   │   ├── auth.py               # POST /auth/login|logout, GET /auth/me, PUT /auth/me/binance-credentials
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
│   │   ├── security.py           # JWT create/decode, password hashing
│   │   ├── encryption.py         # Fernet encrypt/decrypt for per-user Binance credentials
│   │   └── databases/
│   │         ├── database.py     # Async DB connection
│   │         ├── migrations/     # yoyo SQL migrations (001–011)
│   │         └── repositories/   # Data access objects per domain (incl. users_repo.py)
│   ├── services/
│   │   ├── evaluation_worker.py  # Scores past decisions vs realized price (4h/24h/72h horizons)
│   │   ├── metrics_engine.py     # Rolling IC/DA/PnL per user+symbol+horizon+window → signal_metrics
│   │   └── finbert_api.py        # Standalone FinBERT sentiment scoring service
│   ├── retrieval/                # FAISS vector store + embeddings
│   └── ingestion/                # PDF loader + chunking
├── scripts/
│   └── create_user.py            # Admin-only user creation (run: python -m scripts.create_user)
├── k8s/                          # k3s manifests: postgres, api, finbert, frontend, grafana, worker CronJobs
├── grafana/                      # Dashboard JSON + datasource/dashboard provisioning
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

All endpoints except `/auth/login` require authentication. Create a user before calling the API:

```bash
python -m scripts.create_user
```

For a k3s deployment (still unverified against a live cluster), see [k8s/README.md](k8s/README.md).

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
FINBERT_URL=http://localhost:8001

# Postgres
POSTGRES_HOST=localhost

# Auth
# Users are created via `python -m scripts.create_user`, not env vars.
JWT_SECRET_KEY=long_random_secret
JWT_EXPIRY_HOURS=8

# Encryption (for per-user Binance credentials at rest) — generate with:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=generate_a_fernet_key
```

## API Endpoints

### Auth

```
POST /auth/login                       Username + password → httpOnly JWT cookie
POST /auth/logout                      Clear the session cookie
GET  /auth/me                          Currently authenticated username
PUT  /auth/me/binance-credentials      Set/overwrite this user's Binance API key + secret (encrypted at rest)
```

Every other endpoint below requires the session cookie. There is no self-registration — accounts are created with `python -m scripts.create_user`.

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
GET /agent/analyze?symbol=BTCUSDT       Run full multi-agent analysis (default: BTCUSDT)
GET /portfolio/recommendations          Daily safe crypto screener + rebalancing report  [planned]
GET /portfolio/screener                 Raw asset safety scores — top-100 ranked         [planned]
```

### Governance *(planned — Step 1.10)*

```
GET  /policies                  List policies (versioned)                 [planned]
PUT  /policies/{id}             Update policy (creates new version)       [planned]
GET  /risk/limits               Current limits + live exposure vs limits  [planned]
GET  /approvals                 List proposals (filter by status)         [planned]
POST /approvals/{id}/approve                                              [planned]
POST /approvals/{id}/reject                                               [planned]
GET  /audit/{run_id}            Full audit trail for one pipeline run     [planned]
GET  /executions                Reconciled execution history              [planned]
GET  /metrics                   Prometheus scrape endpoint                [planned]
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
- [x] Milestone 9 — React frontend (`frontend/` in this repo): Portfolio, Analyze (decision report cards + Binance order UI), Market Data, Settings (per-user Binance credentials), Login
- [x] Milestone 10 — JWT authentication + multi-user: login page, protected routes, httpOnly cookies, all API endpoints secured; accounts admin-created via `scripts/create_user.py`, per-user encrypted Binance credentials, analysis/portfolio/metrics scoped by `user_id`
- [ ] Milestone 11 — Kubernetes deployment: manifests written for postgres, api, finbert, frontend, grafana, and worker CronJobs (see `k8s/`) — not yet verified against a live k3s cluster
- [x] Milestone 12 — Signal quality monitoring: outcomes store, evaluation worker (4h/24h/72h horizons), metrics engine (rolling IC/DA/PnL per user+symbol+window), Grafana Signal Quality dashboard
- [ ] Milestone 13 — Portfolio intelligence: safe crypto screener, multi-source data aggregation, fee-aware rebalancer
- [ ] Milestone 14 — Real-time messaging: Kafka KRaft broker, ZeroMQ intra-pod, WebSocket gateway pod, Avro Schema Registry
- [ ] Milestone 15 — Python optimisations: NumPy indicators, float risk.py, Redis indicator cache, asyncio, profiling
- [ ] Milestone 16 — C++ engine: 7 modules — indicators (SIMD/AVX2/streaming), risk, orderbook, feed, stats, backtest, precompute
- [ ] Milestone 17 — Price forecasting: LSTM / Temporal Fusion Transformer signal (PyTorch)
- [ ] Milestone 18 — Backtesting + Kafka: walk-forward validation, signal attribution, durable event replay
- [ ] Milestone 19 — RL execution agent: learned position sizing (PPO/SAC, stable-baselines3)
- [ ] Milestone 20 — Neural network agent ensemble: CNN pattern recognition, Neural GARCH volatility, Order Flow LSTM, VAE anomaly detection, Cross-asset LSTM, FinGPT sentiment — all served via ONNX Runtime C++ bridge
- [ ] Milestone 21 — Governance & Control Plane: Risk Gate, Policy Engine, Approval Engine, Audit Engine (deterministic guardrails on LLM output)
- [ ] Milestone 22 — Execution reconciliation: match manual Binance fills to approved proposals
- [ ] Milestone 23 — Full observability: Prometheus scrape endpoint + Alertmanager (Grafana dashboard already done in Milestone 12)

See [docs/ROADMAP.md](docs/ROADMAP.md) for full context, rationale, and implementation details.
