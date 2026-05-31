# Roadmap

R&D roadmap for the Agentic Trading Intelligence Platform.

**Goals:**
- Build a sellable AI trading research product (SaaS / startup)
- Introduce a C++ codebase for performance-critical numerical work

---

## Step 1 — Complete the Agent Pipeline
*Python · LangGraph*

Close the gap between the architecture diagram and the running code.

| Agent | Status | Output |
|---|---|---|
| **News & Sentiment Agent** | ✅ Done | CoinDesk RSS + NewsAPI headlines scored by FinBERT |
| **Correlation Agent** | ✅ Done | BTC/ETH correlation coefficients, diversification score |
| **Strategy Agent** | ✅ Done | BUY / WAIT / AVOID + entry zone + thesis (Ollama LLM) |
| **Critic Agent** | ✅ Done | Challenges the proposal, flags contradictions and ignored risks |
| **Decision Report Agent** | ✅ Done | Final structured report with adjusted confidence score |

**Critic Agent** — receives the full state (all parallel signals + strategy decision) and prompts the LLM to act as a risk-focused adversary: identify contradictions between signals, highlight risks the strategy ignored, and rate severity (low / medium / high). Output feeds the Decision Report Agent.

**Decision Report Agent** — weighs the strategy proposal against the critic's challenges and produces the final report: `final_action`, `confidence` (potentially adjusted down), `bull_case`, `bear_case`, `key_risks`. This is what the human sees and approves.

**AI addition:** The News & Sentiment Agent uses **FinBERT** (`ProsusAI/finbert`) for headline classification — not just an LLM prompt. Each headline is scored on a continuous positive/negative/neutral scale and aggregated into a combined sentiment signal. The inference stack (`torch`, `transformers`) is already installed.

Completing this step produces a coherent end-to-end product with adversarial review built into the pipeline.

---

## Step 1.5 — Kubernetes Deployment + React Frontend + Authentication
*Python · React 18 · TypeScript · k3s · Kubernetes · JWT*

Deploy the platform as independent pods on a self-hosted k3s cluster (Linux VM on VMware Player). Build the React frontend as a separate repo and pod. Add JWT authentication to protect all API endpoints.

---

### Step 1.5a — React Frontend (`frontend/` in this repo)
*React 18 · TypeScript · Tailwind CSS · React Query · React Router v6 · Zustand*

The current vanilla HTML/JS UI is replaced by a proper React application living in a `frontend/` directory inside this repository. It is built and deployed as its own Kubernetes pod. The FastAPI backend is API-only — it no longer serves the static frontend.

**Tech stack:**

| Library | Purpose |
|---|---|
| React 18 + TypeScript | Component framework |
| Tailwind CSS | Styling — no custom CSS files |
| React Query (TanStack) | API fetching, caching, background refetch |
| React Router v6 | Client-side routing, protected routes |
| Zustand | Lightweight state (auth token, active symbol, settings) |
| Recharts | Portfolio charts, IC/DA/PnL trend lines |
| TradingView Lightweight Charts | Candlestick + indicator overlays |

**Pages:**

| Route | Purpose |
|---|---|
| `/login` | Authentication — username + password → JWT |
| `/dashboard` | Main analysis: symbol search, full decision report, Binance order instructions |
| `/portfolio` | Current holdings, risk metrics, unrealized/realized P&L |
| `/screener` | Safe crypto screener — top-100 ranked by safety score |
| `/recommendations` | Daily rebalancing report with trade instructions |
| `/signals` | IC / DA / PnL charts, prediction history |
| `/admin` | LLM provider switch (Ollama ↔ OpenAI), system settings |

**Dashboard page — decision report card** shows all fields from `decision_report`:
- Action badge (BUY / WAIT / AVOID) + confidence
- Entry price, stop loss, take profit, breakeven price
- Risk/reward ratio, position size (% and USDT), total fees
- Binance order instructions (Step 1 + Step 2 OCO) as copy-paste cards
- Critic verdict + severity + challenges
- Bull case / bear case / invalidation condition

**Deployment:** nginx pod serves the built React app (`/`), proxies `/api/*` to the FastAPI pod ClusterIP service.

---

### Step 1.5b — JWT Authentication
*FastAPI · python-jose · passlib · httpOnly cookies*

All API endpoints require a valid JWT. Authentication is username + password — single user (you), credentials stored as a hashed secret in a Kubernetes Secret.

**Flow:**
```
Browser → POST /auth/login (username + password)
        ← httpOnly cookie: access_token (JWT, 8h expiry)

All subsequent requests → cookie sent automatically
FastAPI → validates JWT → grants access

React Router → no valid token → redirect to /login
```

**Why httpOnly cookie (not localStorage):** localStorage is accessible to JavaScript — vulnerable to XSS attacks. httpOnly cookies are invisible to JS and sent automatically by the browser.

**New files:**
- `src/api/auth.py` — `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
- `src/core/security.py` — JWT creation/validation, password hashing
- FastAPI `Depends(get_current_user)` added to all existing routers

**New environment variables:**
```bash
AUTH_USERNAME=your_username
AUTH_PASSWORD_HASH=bcrypt_hash_of_your_password
JWT_SECRET_KEY=long_random_secret
JWT_EXPIRY_HOURS=8
```

---

### Full Pod Topology (Step 1.5 complete)

| Pod | Workload type | Purpose |
|---|---|---|
| `postgres` | StatefulSet + PVC | Persistent database |
| `api` | Deployment | FastAPI + LangGraph — API only, JWT-protected |
| `finbert` | Deployment + PVC | FinBERT inference service |
| `ollama` | Deployment + PVC | Local LLM server |
| `frontend` | Deployment | nginx serving React build, proxies to api |
| `nginx-ingress` | DaemonSet | TLS termination, routes traffic to frontend pod |

**LLM provider switching** — a `ConfigMap` (`llm-config`) holds the active provider (`ollama` or `openai`). The `/admin` page in the React UI switches it live via `POST /admin/llm-provider`.

---

### Backend code changes required

1. Extract FinBERT into standalone FastAPI service (`src/services/finbert_api.py`) with `Dockerfile.finbert`
2. Add `LLMClient` abstraction in `strategy_node` routing to Ollama or OpenAI
3. Add `src/api/auth.py` — JWT login/logout/me endpoints
4. Add `src/core/security.py` — JWT + password utilities
5. Add `Depends(get_current_user)` to all existing routers
6. Add `POST /admin/llm-provider` endpoint

### Frontend directory structure

```
frontend/
├── src/
│   ├── api/          # React Query hooks (useAnalyze, usePortfolio, etc.)
│   ├── components/   # Shared UI components
│   ├── pages/        # One file per route
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Portfolio.tsx
│   │   ├── Screener.tsx
│   │   ├── Recommendations.tsx
│   │   ├── Signals.tsx
│   │   └── Admin.tsx
│   ├── store/        # Zustand stores
│   └── router.tsx    # React Router + protected route wrapper
├── Dockerfile        # nginx + React build
├── nginx.conf        # proxy /api → api pod ClusterIP
└── package.json
```

### Resource requirements for the VM

| Pod | RAM |
|---|---|
| postgres | ~256 MB |
| api | ~512 MB |
| finbert | ~1 GB |
| ollama (llama3.2:3b) | ~4 GB |
| frontend (nginx) | ~64 MB |
| k3s system overhead | ~512 MB |
| **Total** | **~6.5 GB** |

Assign at least **10 GB RAM** to the Linux VM; 16 GB recommended.

---

## Step 1.6 — Signal Quality Monitoring (Test Environment Gate)
*Python · PostgreSQL · Grafana · CronJob*

Before promoting to production, measure whether the agent signals actually have predictive value. This step runs on the test environment (Kubernetes cluster) for 2–4 weeks and produces the evidence needed to trust — or distrust — the system.

**The rule:** do not promote to production until rolling DA > 55% and IC > 0.05 over a 30-day window.

---

### Prediction Frequency — Two-Layer Model

The pipeline has physical constraints that determine how often it can run:

| Bottleneck | Min realistic interval |
|---|---|
| 3× Ollama LLM calls (strategy + critic + report) | ~60–180s total |
| FinBERT news scoring | ~5–10s |
| Binance REST API (multiple signed calls) | 1200 weight/min rate limit |

More importantly, the signals themselves have a natural update frequency determined by the data they consume:

| Node | Data | Meaningful update frequency |
|---|---|---|
| `market_regime` | 250 daily candles, SMA50/200 | Daily |
| `technical_analysis` | 4h OHLCV, RSI/MACD/BB | Every 4h |
| `momentum` | 4h OHLCV, OBV | Every 4h |
| `news_sentiment` | News headlines (RSS + NewsAPI) | Every 1–4h |
| `correlation` | Daily returns | Daily |
| `liquidity` | Order book snapshot | Every 15–30 min |

Running the full pipeline every 10 seconds on daily candles is meaningless — the data does not change. The system is a **4h swing trading signal generator**.

#### Fast layer — every 15–30 minutes
Re-compute order book and momentum indicators only. No LLM, no FinBERT. Detect significant changes (RSI crossing 70/30, spread spike, OBV divergence) and flag them. Does not produce a BUY/WAIT/AVOID decision — produces alerts only.

#### Slow layer — every 4 hours
Full 11-node pipeline run. All signals, all three LLM calls, full decision report. This is the prediction that gets written to the prediction store and evaluated.

**Evaluation horizons** — each 4h prediction is evaluated at:
- **+4h** — short-term accuracy
- **+24h** — daily accuracy
- **+72h** — swing accuracy

---

### Components

#### Prediction Store
Every time `decision_report_node` completes, persist the prediction to a new `predictions` table:

```sql
CREATE TABLE predictions (
    id              SERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    final_action    TEXT NOT NULL,          -- BUY / WAIT / AVOID
    confidence      FLOAT NOT NULL,
    entry_zone      TEXT,
    critic_verdict  TEXT,
    critic_severity TEXT,
    layer           TEXT DEFAULT 'slow',    -- 'slow' (4h full pipeline) or 'fast' (15min alert)
    evaluated_4h    BOOLEAN DEFAULT FALSE,
    evaluated_24h   BOOLEAN DEFAULT FALSE,
    evaluated_72h   BOOLEAN DEFAULT FALSE
);
```

This is a one-line addition to `decision_report_node` — write to DB after returning the result.

#### Evaluation Worker
A Kubernetes `CronJob` that runs every hour. For each unevaluated prediction older than N hours (configurable per symbol — 4h, 24h), it:

1. Fetches the actual price at `timestamp + N` from Binance
2. Computes `actual_return = (price_then - price_now) / price_now`
3. Computes `correct = (final_action == "BUY" and actual_return > 0) or (final_action == "AVOID" and actual_return < 0)`
4. Writes result to an `outcomes` table
5. Marks prediction as `evaluated = TRUE`

```sql
CREATE TABLE outcomes (
    prediction_id INTEGER REFERENCES predictions(id),
    evaluated_at  TIMESTAMPTZ NOT NULL,
    price_at_signal FLOAT,
    price_at_horizon FLOAT,
    actual_return FLOAT,
    correct       BOOLEAN,
    horizon_hours INTEGER
);
```

#### Metrics Engine
A second `CronJob` (runs daily) that aggregates outcomes into a `signal_metrics` table with rolling windows:

| Metric | Formula | Target |
|---|---|---|
| **DA** (Directional Accuracy) | `correct / total predictions` | > 55% |
| **IC** (Information Coefficient) | Pearson correlation of `confidence` vs `actual_return` | > 0.05 |
| **Simulated PnL** | Sum of `actual_return` for BUY signals, `-actual_return` for AVOID | Positive |
| **Avg confidence on correct** | Mean confidence when correct | Should be higher than when wrong |

Computed over rolling 7d, 30d, 90d windows per symbol and in aggregate.

#### Grafana Dashboard
Add a `grafana` pod to the Kubernetes cluster. Connect it to PostgreSQL via the built-in PostgreSQL datasource plugin. No extra infrastructure needed — Grafana reads directly from the same DB.

**Panels:**
- Rolling DA % over time (line chart, 7d / 30d)
- Rolling IC over time
- Simulated cumulative PnL
- Per-symbol breakdown (which symbols the system is best at)
- Prediction volume per day
- Critic verdict distribution (how often agree / caution / reject)
- Confidence calibration: does higher confidence correlate with better outcomes?

---

### Pod addition to Step 1.5 topology

| Pod | Workload type | Purpose |
|---|---|---|
| `signal-scheduler` | CronJob (every 4h) | Triggers full pipeline run, writes to prediction store |
| `fast-monitor` | CronJob (every 15 min) | Recomputes order book + momentum, emits alerts only |
| `evaluation-worker` | CronJob (hourly) | Fetch actual prices, score predictions at +4h/+24h/+72h |
| `metrics-engine` | CronJob (daily) | Aggregate IC / DA / PnL into metrics table |
| `grafana` | Deployment + PVC | Dashboard — reads from PostgreSQL |

---

### New DB migrations required

- `008_predictions.sql` — `predictions` table
- `009_outcomes.sql` — `outcomes` table
- `010_signal_metrics.sql` — `signal_metrics` rolling metrics table

---

### Production gate checklist

Before promoting from test to production environment:

- [ ] At least 100 evaluated predictions
- [ ] Rolling 30d DA > 55%
- [ ] Rolling 30d IC > 0.05
- [ ] No single symbol dominating predictions (diversified coverage)
- [ ] Grafana dashboard shows stable, not degrading, metrics over time

---

## Step 1.7 — Portfolio Intelligence (Safe Crypto Screener + Rebalancer)
*Python · CoinGecko · GitHub API · DeFiLlama · FRED · LangGraph*

A separate module that answers two questions on a daily schedule:
1. **Which assets are safe and worth holding right now?** — screener scores the top-100 cryptos
2. **What should I do with my current portfolio?** — rebalancer computes exact trades to reach the target allocation

This is a second LangGraph graph running independently from the 4h trading signal pipeline.

---

### Data Sources

| Source | Data pulled | Cost |
|---|---|---|
| **CoinGecko API** | Market cap rank, 24h volume, price, developer stats, community size | Free (30 req/min) |
| **Alternative.me** | Fear & Greed Index (0–100) | Free |
| **DeFiLlama API** | TVL for DeFi protocols | Free |
| **GitHub API** | Commit frequency, contributors, open issues (last 30d) | Free |
| **FRED API** | Macro — US interest rates, CPI, DXY (dollar index) | Free |
| **Reddit API** | r/cryptocurrency, r/bitcoin post/comment sentiment | Free tier |
| **CoinDesk RSS** | Already integrated — reused here | Free |
| **NewsAPI** | Already integrated — reused here | Free tier |
| *Glassnode* | On-chain: active addresses, exchange flows | Paid — optional later |
| *LunarCrush* | Social dominance score | Paid — optional later |

---

### Safety Scoring Model

Each asset in the top-100 receives a composite score 0–100:

| Metric | Weight | Source | Rationale |
|---|---|---|---|
| Market cap rank | 20% | CoinGecko | Top 30 = more liquid, less manipulation risk |
| Liquidity ratio (24h vol / mcap) | 15% | CoinGecko | Low liquidity = hard to exit at price |
| 30d realised volatility | 15% | CoinGecko | Lower vol = more predictable, safer |
| Developer activity (commits 30d) | 15% | GitHub API | Active dev = project is alive |
| News sentiment score | 10% | FinBERT (reused) | Negative press = elevated risk |
| Fear & Greed Index | 10% | Alternative.me | Market-wide risk level |
| Portfolio correlation | 10% | Computed internally | Low correlation = diversification benefit |
| TVL (DeFi assets only) | 5% | DeFiLlama | Protocol adoption signal |

Output: ranked shortlist of top-10 safe assets with score breakdown per metric.

---

### Components

```
PortfolioIntelligenceGraph (LangGraph)
  │
  ├── data_aggregation_node      — parallel fetch from CoinGecko, GitHub, DeFiLlama, FRED, Reddit
  │
  ├── asset_screener_node        — score all top-100 assets, rank by safety score
  │
  ├── portfolio_optimizer_node   — compare current Binance holdings vs screener shortlist
  │     └── compute target allocation using risk-parity or equal-weight across top-N
  │
  ├── rebalancing_engine_node    — compute exact trades to reach target allocation
  │     └── respects: min order 100 USDT, fee costs, locked funds, existing open orders
  │
  └── recommendation_report_node — LLM synthesises screener + rebalancing into final report
```

---

### Rebalancing Engine Rules

- Minimum trade size: **100 USDT** (Binance minimum)
- Fee-aware: all trade sizes account for the 0.1% round-trip fee (reuses `_FEE_RATE` from `decision_report`)
- Locked funds excluded from rebalancing calculation
- Generates Binance order parameters in the same format as `decision_report` (`LIMIT` orders, no OCO needed for rebalancing)
- Outputs: list of `{ symbol, side, amount_usdt, current_pct, target_pct, instruction }`

---

### New API Endpoint

```
GET /portfolio/recommendations     Daily screener + rebalancing report
GET /portfolio/screener            Raw asset scores (top-100 ranked)
```

---

### New K8s Pod

| Pod | Workload type | Schedule |
|---|---|---|
| `portfolio-optimizer` | CronJob | Daily at 08:00 UTC |

---

### New DB Migration

- `011_screener_scores.sql` — daily asset scores per symbol (feeds Grafana trend chart showing how scores evolve over time)

---

## Step 1.8 — Real-Time Infrastructure: Kafka + ZeroMQ + FastAPI WebSocket
*Apache Kafka (KRaft) · ZeroMQ · FastAPI WebSocket · Python · C++*

Add a production-grade, durable, replayable messaging backbone. Kafka is the primary inter-service bus for the entire platform — chosen now rather than later to avoid a painful migration when backtesting, RL, and LSTM training demand it.

---

### Why Kafka From the Start

| Requirement | Needed by | Without Kafka |
|---|---|---|
| Message persistence — survive pod restart | Evaluation worker | Predictions lost on crash |
| Replay historical events | Backtesting (Step 5), RL training (Step 6) | Must rebuild from scratch |
| Multiple independent consumers of same stream | Indicator engine + backtester + RL agent + LSTM trainer | Redis delivers to only one |
| 30-day market tick retention | ML training dataset | Not possible with Redis |
| Exactly-once delivery of predictions | Evaluation worker, DB writer | Duplicates or gaps |
| Consumer groups — horizontal scaling | Multiple API pods | Manual coordination |

Kafka adds ~512MB RAM on a 16GB VM — 3% of available memory. Setting it up once now is far cheaper than migrating three dependent systems later.

---

### Kafka Topic Design

| Topic | Producers | Consumers | Retention | Purpose |
|---|---|---|---|---|
| `market.ticks.{SYMBOL}` | C++ feed handler | indicator engine, fast-monitor, backtester, RL agent | 30 days | Real-time price ticks |
| `market.candles.1h.{SYMBOL}` | signal-scheduler | technical_analysis, regime, precompute | 90 days | Hourly OHLCV candles |
| `market.candles.4h.{SYMBOL}` | signal-scheduler | full pipeline trigger | 90 days | 4h OHLCV candles |
| `market.orderbook.{SYMBOL}` | C++ feed handler | liquidity node, backtester | 7 days | L2 order book snapshots |
| `analysis.complete` | api | evaluation-worker, websocket-gateway, portfolio-optimizer | 7 days | Full pipeline results |
| `predictions.new` | decision_report_node | evaluation-worker, DB writer | 30 days | Predictions to score |
| `signals.alerts` | fast-monitor | websocket-gateway, evaluation-worker | 3 days | RSI/spread spike alerts |
| `portfolio.updated` | api | websocket-gateway | 1 day | Portfolio snapshots |
| `screener.updated` | portfolio-optimizer | websocket-gateway | 1 day | Daily screener results |

All topics use **Avro schemas** with Schema Registry for type safety as the system grows.

---

### Three-Layer Messaging Architecture

```
Binance WebSocket (cloud)
  └── Layer 1: ZeroMQ (intra-pod, <0.1ms)
        └── C++ feed handler → ZeroMQ PUB
              └── ZeroMQ SUB → Kafka Producer
                    └── Layer 2: Kafka (inter-pod, durable, replayable)
                          ├── market.ticks.BTCUSDT
                          ├── market.orderbook.BTCUSDT
                          └── analysis.complete
                                └── Layer 3: WebSocket Gateway
                                      └── FastAPI WS /ws/live → Browser (React)
```

#### Layer 1 — ZeroMQ (intra-pod)
Embedded in the C++ feed handler pod. No broker, sub-millisecond. Bridges Binance WebSocket → Kafka without Python GIL involvement. The C++ module writes directly to the Kafka producer via `librdkafka`.

#### Layer 2 — Kafka KRaft (inter-pod)
Single-broker KRaft cluster (no ZooKeeper). Deployed via Helm chart on k3s. All inter-service communication is a Kafka producer/consumer pair — no direct HTTP calls between pods for event-driven flows.

**Consumer groups:**
- `indicator-engine` — consumes `market.ticks.*`, updates streaming indicators
- `evaluation-group` — consumes `predictions.new`, scores at +4h/+24h/+72h
- `ws-gateway` — consumes all UI-relevant topics, fans out to browser WebSockets
- `backtester` (Step 5) — replays `market.ticks.*` from arbitrary offset

#### Layer 3 — FastAPI WebSocket Gateway (pod → browser)
A dedicated `websocket-gateway` pod subscribes to Kafka topics and forwards events to connected browser clients. Decoupled from the `api` pod — the gateway can restart without affecting the API.

```
WS /ws/live    — streams: analysis_complete, price_alert, portfolio_update, screener_update
```

**React side:** `useWebSocket` hook (Zustand) dispatches events to page stores. Dashboard updates its decision report card live when `analysis.complete` fires.

---

### Redis Role (Reduced)

Redis stays in the stack but **only as a cache** — not as a message bus:
- Pre-computed indicator results (Step 1.9 + Step 3 Module 7)
- Session/JWT token storage
- Rate limiting counters

All messaging goes through Kafka.

---

### New Pods (Step 1.8)

| Pod | Workload type | RAM | Purpose |
|---|---|---|---|
| `kafka` | StatefulSet + PVC | ~512 MB | KRaft broker — durable event log |
| `schema-registry` | Deployment | ~256 MB | Avro schema validation |
| `websocket-gateway` | Deployment | ~128 MB | Kafka → browser WebSocket fan-out |
| `redis` | Deployment | ~64 MB | Indicator cache + JWT store |

---

### Updated Full Pod Topology (after Step 1.8)

| Pod | Purpose |
|---|---|
| `postgres` | Persistent DB — analysis history, predictions, portfolio |
| `kafka` | Durable event log — all inter-service messaging |
| `schema-registry` | Avro schemas for Kafka topics |
| `redis` | Indicator cache + JWT store |
| `api` | FastAPI + LangGraph — publishes to Kafka |
| `finbert` | FinBERT inference service |
| `ollama` | LLM server |
| `frontend` | React app + nginx proxy |
| `websocket-gateway` | Kafka consumer → browser WebSocket |
| `nginx-ingress` | TLS + routing |
| `signal-scheduler` | 4h pipeline CronJob — triggers via Kafka |
| `fast-monitor` | 15min alert CronJob — publishes to `signals.alerts` |
| `evaluation-worker` | Hourly — consumes `predictions.new` from Kafka |
| `metrics-engine` | Daily — reads outcomes, writes IC/DA/PnL |
| `portfolio-optimizer` | Daily — publishes to `screener.updated` |

**Total VM RAM estimate:**

| Pod | RAM |
|---|---|
| postgres | ~256 MB |
| kafka | ~512 MB |
| schema-registry | ~256 MB |
| redis | ~64 MB |
| api | ~512 MB |
| finbert | ~1 GB |
| ollama (llama3.2:3b) | ~4 GB |
| frontend + nginx | ~64 MB |
| websocket-gateway | ~128 MB |
| k3s + system | ~512 MB |
| CronJob pods (idle) | ~256 MB |
| **Total** | **~7.5 GB** |

16 GB VM recommended. 10 GB minimum (Ollama will be the constraint).

---

### New API Endpoints

```
WS  /ws/live         Real-time event stream (via websocket-gateway pod)
GET /ws/status       Gateway health + connected client count
```

---

## Step 1.9 — Python Performance Quick Wins (Pre-C++ Optimization)
*Python · NumPy · asyncio · Redis cache*

Profile first, then fix the confirmed bottlenecks in Python before writing any C++. These changes take hours and deliver significant gains on the CPU-bound parts of the pipeline.

**Rule:** never optimize without measuring. Run cProfile on a full pipeline execution first.

---

### Quick Wins

| Change | Current | After | Effort |
|---|---|---|---|
| Replace `Decimal` with `float` in `risk.py` | ~50× slower than C double | Native float speed | 30 min |
| Rewrite `indicators.py` loops with NumPy vectorisation | Python for-loops | 10–50× faster | 2–3h |
| Cache indicator results in Redis by `(symbol, interval, candle_hash)` | Recomputes every request | Skip if candles unchanged | 3h |
| `asyncio.gather` for parallel Binance API calls in `portfolio_snapshot` | Sequential HTTP calls | Concurrent, no waiting | 1h |
| Streaming EMA/RSI — O(1) update on new candle, not O(n) recompute | Full recompute each time | Single operation per tick | 2h |

---

### Profiling Setup

Add a `/debug/profile` endpoint (dev only, disabled in production) that runs `cProfile` over one full pipeline execution and returns a flamegraph-compatible JSON. This tells you exactly which lines are slow before Step 3 C++ work begins.

---

## Step 2 — ML-Based Regime Detection
*~2 weeks · Python · scikit-learn / hmmlearn*

Replace the rule-based `market_regime_node` with a trained probabilistic model.

**Models to implement:**
- **Hidden Markov Model (HMM)** — 3 hidden states (bull / bear / sideways), Gaussian emissions over OHLCV + volatility features. Industry-standard approach at macro hedge funds.
- **Gaussian Mixture Model (GMM)** — simpler baseline for comparison.

**Features:** log-returns, realised volatility (21-day), volume z-score, funding rate (futures), RSI.

**Output change:** instead of a string label the node emits `{ "regime": "bull", "probability": 0.87, "model": "hmm" }`. Downstream agents consume the probability, not just the label.

Train on historical BTC/ETH OHLCV pulled from Binance. Persist the fitted model as a `.pkl` / ONNX file so it can be loaded at startup without retraining.

---

## Step 3 — C++ Engine + ONNX Integration
*~3 weeks · C++20 · pybind11 · ONNX Runtime*

Introduce a C++ extension that handles all performance-critical numerical work. Python orchestrates agents; C++ handles heavy computation.

**Build system:** CMake 3.28 + `pybind11`. The extension is imported in Python exactly like any other module (`from indicators_cpp import compute_rsi`).

**ONNX bridge:** Export the HMM/GMM from Step 2 to ONNX. Run inference from C++ using `onnx-runtime`. Full pipeline: Python trains → ONNX serialises → C++ serves.

---

### C++ Modules Map

Every module below targets C++20 or later. Each module has three tiers: **baseline** (correct, fast), **SIMD** (vectorised with AVX2), and **streaming** (O(1) incremental update per new candle).

**Profiling requirement:** before writing any module, run Step 1.9 profiling to confirm the Python version is actually the bottleneck. Never optimise blindly.

---

#### Module 1 — Indicator Engine (`cpp/indicators/`)
*Replaces `src/agents/tools/indicators.py`*

Compute RSI, EMA, SMA, MACD, Bollinger Bands, ATR, OBV on large price series without the Python GIL.

**Tier 1 — Baseline C++20:**
- `std::span<const double>` — non-owning view into the caller's price array, zero-copy
- `std::ranges::transform` / `std::views::drop` — functional pipeline over price windows
- **Concepts** (`Arithmetic`, `PriceSeries`) — constrain templates so `compute_rsi<int>` fails at compile time
- `consteval` — compile-time validation of period parameters (period > 0)

**Tier 2 — SIMD (AVX2):**
- EMA inner loop: process 4 doubles per cycle with `_mm256_fmadd_pd` (fused multiply-add)
- Bollinger Band std dev: vectorised variance accumulation
- OBV: vectorised sign comparison + conditional accumulation
- Compile-time CPU feature detection — falls back to scalar if AVX2 unavailable

**Tier 3 — Streaming (O(1) per tick):**
- `StreamingEMA` class: maintains running state (`prev_ema`), updates in one multiply-add
- `StreamingRSI` class: maintains `avg_gain` / `avg_loss` with Wilder smoothing
- `StreamingBollinger` class: Welford's online algorithm for rolling mean + variance
- Exposed to Python via pybind11 as stateful objects — ZeroMQ feed pushes ticks directly

```cpp
template <Arithmetic T>
auto compute_rsi(std::span<const T> closes, int period = 14) -> std::vector<double>;

class StreamingEMA {
    double update(double price) noexcept;  // O(1), no allocation
};
```

---

#### Module 2 — Risk Calculator (`cpp/risk/`)
*Replaces `src/agents/tools/risk.py`*

HHI, VaR (historical simulation), CVaR, Kelly criterion, P&L with weighted average cost basis.

**Key change from Python version:** replaces Python `Decimal` (50× slower) with `double`. For portfolio risk metrics the precision difference is irrelevant — HHI and concentration percentages do not require arbitrary precision arithmetic.

**C++20 features used:**
- **Concepts** (`PortfolioAsset`, `PriceMap`) — named requirements replace `dict[str, Any]`
- `std::ranges::sort`, `std::ranges::accumulate` — clean range-based algorithms
- `std::span` — pass price arrays from Python without copying
- Designated initializers — `RiskResult{ .hhi = 0.12, .var_95 = 1500.0 }`
- `[[nodiscard]]` on every function that returns a metric

---

#### Module 3 — Order Book Processor (`cpp/orderbook/`)
*Replaces inline computation in `src/agents/tools/nodes/liquidity.py`*

Parse L2 snapshots, compute bid/ask imbalance, VWAP, and slippage estimate for a given order size.

**C++20 features used:**
- `std::span<const PriceLevel>` — view into bid/ask arrays
- **Three-way comparison (`<=>`)** — `PriceLevel` is sortable with `auto operator<=>`
- `std::ranges::fold_left` (C++23 preview available in GCC 13) — cumulative depth calculation
- `std::atomic_ref<double>` — lock-free imbalance accumulation across threads

```cpp
struct PriceLevel {
    double price;
    double qty;
    auto operator<=>(const PriceLevel&) const = default;
};

double compute_slippage(std::span<const PriceLevel> asks, double order_size_usdt);
```

---

#### Module 4 — WebSocket Feed Handler (`cpp/feed/`)
*New — real-time Binance order book streaming*

Connect to the Binance WebSocket Streams API, maintain a local order book, and push updates to the Python layer via a queue.

**C++20 features used:**
- **Coroutines (`co_await`, `co_yield`)** — async I/O without callbacks
- `std::jthread` + `std::stop_token` — auto-joining, cooperatively cancellable background thread; no manual `join()` or flag polling
- `std::stop_callback` — register cleanup on cancellation
- `std::barrier` — synchronise snapshot + incremental update phases during order book initialisation

```cpp
// Coroutine that yields order book deltas
Task<OrderBookDelta> stream_order_book(std::string_view symbol, std::stop_token st);
```

---

#### Module 5 — Backtesting Engine (`cpp/backtest/`)
*New — event-driven backtester for Step 5*

Replay historical OHLCV candles through the agent signal pipeline and compute strategy performance.

**C++20 features used:**
- `std::generator<Event>` (C++23, available via GCC 14 / clang 17) or manual coroutine — lazy event stream over millions of candles
- **Concepts** (`Strategy`, `EventHandler`) — any class with `.on_candle()` and `.on_signal()` satisfies the constraint; no inheritance required
- `std::chrono::utc_clock` — nanosecond timestamps with correct leap-second handling
- `std::variant<CandleEvent, SignalEvent, FillEvent>` + `std::visit` — type-safe event dispatch without virtual dispatch overhead
- `std::mdspan` (C++23) — 2D view into the OHLCV matrix without copying

```cpp
template <Strategy S>
BacktestResult run(S& strategy, std::span<const Candle> candles);
```

---

#### Module 6 — Statistics Library (`cpp/stats/`)
*Supports Modules 1–5 and Step 2 HMM inference*

Rolling statistics, correlation matrix, Sharpe/Sortino ratio, covariance — used by multiple modules.

**C++20 features used:**
- `std::ranges` algorithms throughout — `std::ranges::inner_product`, `std::ranges::minmax`
- **Concepts** (`Numeric`, `RandomAccessRange`) — constrain all statistical functions
- `consteval double confidence_to_z(double p)` — compile-time Z-score lookup
- `std::latch` — wait for parallel correlation computations to finish before assembling the matrix

**Streaming additions:**
- Welford's online algorithm for rolling mean + variance — O(1) update, numerically stable
- Online Pearson correlation — maintains `sum_xy`, `sum_x2`, `sum_y2` incrementally
- Rolling Sharpe — updated on each new return observation without recomputing full window

---

#### Module 7 — Pre-Computation Pipeline (`cpp/precompute/`)
*New — computes indicators ahead of request time*

A background `std::jthread` that watches for new candle data (via ZeroMQ SUB socket from Module 4), recomputes all indicators incrementally, and stores results in a Redis-compatible shared buffer. When the Python pipeline runs, `technical_analysis_node` reads pre-computed results instead of computing from scratch.

**Architecture:**
```
Binance WebSocket
  └── Module 4 (ZeroMQ PUB)
        └── Module 7 (ZeroMQ SUB → StreamingEMA/RSI/BB → Redis HSET)
              └── Python technical_analysis_node (Redis HGET — microseconds)
```

**C++20 features used:**
- `std::jthread` + `std::stop_token` — background precompute thread, cleanly cancellable
- `std::shared_mutex` — readers (Python via pybind11) never block each other
- `std::atomic<uint64_t>` — lock-free candle sequence counter
- `std::chrono::utc_clock` — nanosecond-precision candle timestamps

**Result:** `technical_analysis_node` latency drops from ~200ms (Python loop on 500 candles) to ~1ms (Redis read of pre-computed result).

---

### C++20 Features Coverage Summary

| Feature | Module(s) |
|---|---|
| Concepts | 1, 2, 3, 5, 6 |
| `std::span` | 1, 2, 3 |
| `std::ranges` / views | 1, 2, 6 |
| Coroutines (`co_await`, `co_yield`) | 4, 5 |
| `std::jthread` + `std::stop_token` | 4, 7 |
| Three-way comparison (`<=>`) | 3 |
| Designated initializers | 2 |
| `consteval` | 1, 6 |
| `std::atomic_ref` / `std::atomic` | 3, 7 |
| `std::barrier` / `std::latch` | 4, 6 |
| `std::shared_mutex` | 7 |
| `std::format` | 1 |
| `std::variant` + `std::visit` | 5 |
| AVX2 SIMD intrinsics | 1 |
| Welford's online algorithm | 6, 7 |
| ONNX Runtime (C++ API) | 2 (regime inference) |
| ZeroMQ integration | 4, 7 |

| Feature | Module(s) |
|---|---|
| Concepts | 1, 2, 3, 5, 6 |
| `std::span` | 1, 2, 3 |
| `std::ranges` / views | 1, 2, 6 |
| Coroutines (`co_await`, `co_yield`) | 4, 5 |
| `std::jthread` + `std::stop_token` | 4 |
| Three-way comparison (`<=>`) | 3 |
| Designated initializers | 2 |
| `consteval` | 1, 6 |
| `std::atomic_ref` | 3 |
| `std::barrier` / `std::latch` | 4, 6 |
| `std::format` | 1 |
| `std::variant` + `std::visit` | 5 |
| ONNX Runtime (C++ API) | 2 (regime inference) |

---

## Step 4 — Price Forecasting with LSTM / Temporal Fusion Transformer
*~2 weeks · Python · PyTorch*

Add a deep learning price forecasting model as one additional signal input to the analysis agent. CUDA and `torch` are already installed.

**Model options:**
- **LSTM** — simpler, easier to explain, good baseline
- **Temporal Fusion Transformer (TFT)** — state-of-the-art for multi-horizon time series, interpretable attention weights

**Input features:** OHLCV, volume, RSI, MACD, funding rate, regime probability from Step 2.

**Output:** directional probability for next 4h / 24h candle + uncertainty interval (Monte Carlo dropout or quantile loss).

Frame this as *one signal among many* — the analysis agent weighs it alongside technical, regime, and sentiment signals, not as a direct trade oracle.

Do not use raw price predictions for direct trade execution.

---

## Step 5 — Backtesting + Signal Evaluation
*~2 weeks · Python*

Measure whether the agent signals have statistical edge before trusting them.

**What to build:**
- Event-driven backtester that replays historical candles through the agent pipeline
- Signal recorder that persists agent outputs to a database (Postgres + TimescaleDB)
- Walk-forward validation to test signal decay over time
- Per-agent contribution metrics: which node (momentum vs regime vs LSTM) adds the most predictive value

**Key metrics:** Sharpe ratio, max drawdown, hit rate, average holding period, slippage-adjusted return.

The signal contribution analysis is effectively **feature importance for the agent ensemble** — a novel framing that connects LangGraph multi-agent systems to classical quant factor research.

---

## Step 6 — Reinforcement Learning Execution Agent
*~3 weeks · Python · PyTorch · stable-baselines3*

Replace the fixed Kelly / rule-based position sizing in the Strategy Agent with a learned policy.

**Problem framing:**
- **State:** all agent outputs (regime probability, sentiment score, technical signals, LSTM forecast, order book features)
- **Action:** position size as a fraction of portfolio (continuous action space)
- **Reward:** risk-adjusted return (Sharpe-style), penalise drawdown and overtrading

**Environment:** simulated order book from historical Binance data. Use `gymnasium` to wrap it.

**Framework:** `stable-baselines3` (PPO or SAC) for initial training. Custom PyTorch policy for production.

This is the frontier piece that differentiates the platform from rule-based systems. RL for execution and position sizing allows the system to learn optimal behaviour directly from market microstructure data rather than relying on fixed rules.

---

## Step 7 — Neural Network Agent Ensemble
*Python · PyTorch · ONNX · pybind11 · LangGraph*

Extend the LangGraph pipeline with specialised neural network agents running as independent inference pods. Each agent is a parallel node — same pattern as the existing 7 nodes — but produces a learned signal rather than a rule-based one. All models are exported to ONNX and served from C++ via the ONNX Runtime bridge built in Step 3.

---

### How They Fit the Graph

New agents join the existing parallel fan-out. The strategy node prompt already accepts any number of signal inputs — adding agents is additive, nothing in the existing pipeline changes.

```
portfolio_snapshot
  → [...existing 7 nodes (technical, regime, momentum, etc.)...]
  → [price_forecast_node]        ← Step 4 (LSTM/TFT), extended here
  → [pattern_recognition_node]   ← CNN chart pattern detector
  → [volatility_forecast_node]   ← Neural GARCH
  → [order_flow_node]            ← LSTM on L2 order book
  → [anomaly_detection_node]     ← Autoencoder
  → [cross_asset_node]           ← Multivariate LSTM
  → [sentiment_llm_node]         ← FinGPT / FinLLaMA (replaces FinBERT)
  → strategy → critic → decision_report → END
```

Each node calls its inference pod over HTTP (ClusterIP), identical to the FinBERT pod pattern established in Step 1.5.

---

### Agents

#### Agent 1 — Pattern Recognition (`nn/pattern/`)
*CNN on OHLCV chart images*

Detects classical chart patterns that rule-based indicators miss: head & shoulders, double top/bottom, ascending/descending wedge, bull/bear flag, cup and handle.

**Architecture:** 2D CNN treating a rolling 64-candle OHLCV window as a multi-channel image (open, high, low, close, volume as channels). Trained on labelled historical patterns with known outcomes.

**Output:** `{ "pattern": "head_and_shoulders", "confidence": 0.82, "bias": "bearish", "target_pct": -8.3 }`

**Training data:** Binance historical OHLCV (already stored in PostgreSQL from Step 1.6 prediction store). Label using known pattern definitions + forward returns.

---

#### Agent 2 — Volatility Forecasting (`nn/volatility/`)
*Neural GARCH — LSTM over realised volatility*

Predicts next-period volatility — directly improves stop loss placement and position sizing. Current system uses ATR as a proxy; this replaces it with a learned forecast.

**Architecture:** LSTM trained on `[log_return, realised_vol_21d, ATR_pct, funding_rate]`. Outputs volatility estimate for next 4h and 24h.

**Output:** `{ "vol_4h_pct": 2.3, "vol_24h_pct": 4.1, "vol_regime": "expanding" }`

**Integration:** `decision_report_node` uses `vol_4h_pct` instead of `ATR14` for SL distance when this agent is available.

---

#### Agent 3 — Order Flow (`nn/orderflow/`)
*LSTM on L2 order book snapshots*

Predicts short-term price direction from microstructure — bid/ask imbalance, VWAP divergence, large order absorption. Captures information invisible to OHLCV-based indicators.

**Architecture:** LSTM over a sequence of 20 L2 snapshots (20 bid levels × 20 ask levels × quantity). Input comes directly from Kafka `market.orderbook.{SYMBOL}`.

**Output:** `{ "direction": "bullish", "confidence": 0.71, "horizon_minutes": 30 }`

---

#### Agent 4 — Anomaly Detection (`nn/anomaly/`)
*Autoencoder on the full signal vector*

Detects market conditions unlike anything in the training set — flash crashes, manipulation, black swan events. When reconstruction error exceeds threshold, automatically reduces confidence on the final decision.

**Architecture:** Variational Autoencoder (VAE) trained on all 14 node outputs (the full `TradingDecisionState` signal vector). High reconstruction error = anomalous regime.

**Output:** `{ "anomaly_score": 0.94, "is_anomalous": true, "description": "order book depth 4 std devs below 90d mean" }`

**Integration:** `decision_report_node` caps `confidence` at `0.3` when `is_anomalous = true`.

---

#### Agent 5 — Cross-Asset (`nn/crossasset/`)
*Multivariate LSTM across crypto + macro*

Detects macro-driven moves in crypto before they fully propagate. Trained on the joint dynamics of BTC, ETH, DXY (dollar index), Gold, S&P 500 futures, and US 10y yield.

**Architecture:** Multivariate LSTM with attention over `[BTC, ETH, DXY, GOLD, SPX, US10Y]` time series. Macro data from FRED API (already planned in Step 1.7).

**Output:** `{ "macro_bias": "risk_off", "crypto_macro_divergence": 0.73, "signal": "bearish" }`

---

#### Agent 6 — Sentiment LLM (`nn/sentiment_llm/`)
*FinGPT or FinLLaMA — replaces FinBERT*

Replaces the current FinBERT headline scorer with a full financial large language model. FinBERT classifies positive/negative/neutral per headline in isolation. A financial LLM understands context, cause-and-effect, and can summarise multiple conflicting headlines into a nuanced view.

**Model options:**
- **FinGPT** — open source, fine-tuned on financial data, runs locally
- **FinLLaMA** — LLaMA fine-tuned on Bloomberg/Reuters financial corpus

**Output:** same format as current `news_sentiment` node — fully backward compatible. The `news_sentiment` node in the graph is replaced; nothing else changes.

---

### Inference Pod Architecture

Each agent is a standalone FastAPI inference service — same pattern as the `finbert` pod:

| Pod | Model | RAM | Inference time |
|---|---|---|---|
| `nn-pattern` | CNN (ResNet-18 scale) | ~512 MB | ~20ms |
| `nn-volatility` | LSTM | ~256 MB | ~5ms |
| `nn-orderflow` | LSTM | ~256 MB | ~10ms |
| `nn-anomaly` | VAE | ~256 MB | ~5ms |
| `nn-crossasset` | Multivariate LSTM | ~512 MB | ~15ms |
| `nn-sentiment` | FinGPT / FinLLaMA | ~4 GB | ~200ms |

All models exported to **ONNX** and served via the C++ ONNX Runtime bridge from Step 3 — Python pods call C++ inference, not PyTorch directly. This removes PyTorch from the serving path entirely and cuts inference latency 3–5×.

---

### Training Pipeline

All models train on data already in the system:

| Model | Training data source |
|---|---|
| Pattern CNN | PostgreSQL OHLCV + labelled pattern library |
| Volatility LSTM | PostgreSQL OHLCV — realised vol computed from Step 1.9 |
| Order Flow LSTM | Kafka `market.orderbook.*` retained 30 days (Step 1.8) |
| Anomaly VAE | Signal vectors from prediction store (Step 1.6) |
| Cross-asset LSTM | PostgreSQL OHLCV + FRED macro data (Step 1.7) |
| Sentiment LLM | Fine-tune on CoinDesk + NewsAPI headlines already collected |

Training runs as Kubernetes `Job` resources (one-off), not CronJobs. Re-train on demand when model performance degrades (detected via Grafana IC/DA/PnL dashboard from Step 1.6).

---

## Summary

| Step | Focus | AI / Tech | Status |
|---|---|---|---|
| 1 | Complete agent pipeline | FinBERT, Ollama LLM, LangGraph | ✅ Done |
| 1.5a | React frontend | React 18, TypeScript, Tailwind, React Query, Recharts | 🔲 Next |
| 1.5b | JWT authentication | python-jose, passlib, httpOnly cookies | 🔲 Next |
| 1.5c | Kubernetes deployment | k3s, 7 pods (+ redis) | 🔲 Next |
| 1.6 | Signal quality monitoring | Prediction store, eval worker, IC/DA/PnL, Grafana | 🔲 Test env gate |
| 1.7 | Portfolio intelligence | Safe crypto screener + rebalancer, multi-source data | 🔲 Planned |
| 1.8 | Real-time messaging | Kafka KRaft (inter-pod), ZeroMQ (intra-pod), WebSocket gateway (browser) | 🔲 Planned |
| 1.9 | Python optimisations | NumPy indicators, float risk.py, Redis cache, asyncio, profiling | 🔲 Pre-C++ gate |
| 2 | ML regime detection | HMM, GMM (scikit-learn / hmmlearn) | 🔲 Planned |
| 3 | C++ engine + ONNX | 7 modules: indicators (SIMD), risk, orderbook, feed, backtest, stats, precompute | 🔲 Planned |
| 4 | Price forecasting | LSTM / TFT (PyTorch) | 🔲 Planned |
| 5 | Backtesting | Walk-forward, signal attribution — replays Kafka topics from arbitrary offset | 🔲 Planned |
| 6 | RL position sizing | PPO / SAC (stable-baselines3) | 🔲 Planned |
| 7 | Neural network agent ensemble | CNN patterns, Neural GARCH, Order Flow LSTM, VAE anomaly, Cross-asset LSTM, FinGPT | 🔲 Planned |

**C++ modules inside Step 3:**

| Module | Replaces | Key C++20 features |
|---|---|---|
| `cpp/indicators/` | `indicators.py` | Concepts, `std::span`, `std::ranges`, `consteval` |
| `cpp/risk/` | `risk.py` | Concepts, designated initializers, `std::ranges` |
| `cpp/orderbook/` | inline liquidity compute | `std::span`, `<=>`, `std::atomic_ref` |
| `cpp/feed/` | Python WebSocket (new) | Coroutines, `std::jthread`, `std::stop_token`, `std::barrier` |
| `cpp/backtest/` | Python backtester (new) | `std::generator`, Concepts, `std::variant`, `std::visit` |
| `cpp/stats/` | inline stats (new) | Concepts, `std::ranges`, `std::latch`, `consteval` |

Steps 1 through 6 together form a complete AI trading research platform — from signal generation through backtesting to adaptive execution.
