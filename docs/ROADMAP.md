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

## Step 1.5 — Kubernetes Deployment (24/7 Self-Hosted)
*Python · Docker · k3s · Kubernetes*

Deploy the platform as independent pods on a self-hosted k3s cluster (Linux VM on VMware Player). Each concern becomes its own independently scalable and restartable unit.

**Target pod topology:**

| Pod | Workload type | Purpose |
|---|---|---|
| `postgres` | StatefulSet + PVC | Persistent database (market data, analysis history) |
| `api` | Deployment | FastAPI + LangGraph orchestrator — stateless, horizontally scalable |
| `finbert` | Deployment + PVC | FinBERT inference as its own HTTP service (avoids 2GB API image) |
| `ollama` | Deployment + PVC | Local LLM server — models stored in a PersistentVolumeClaim |
| `nginx-ingress` | DaemonSet | TLS termination + routing |

**LLM provider switching** — a `ConfigMap` (`llm-config`) holds the active provider (`ollama` or `openai`). An admin API endpoint allows switching live from the UI without restarting pods. The `strategy_node` uses a thin `LLMClient` wrapper that reads this config at call time.

**Code changes required:**
1. Extract FinBERT inference into a standalone FastAPI service (`src/services/finbert_api.py`) with its own `Dockerfile.finbert`. The `news_sentiment_node` becomes an HTTP call to the finbert pod's ClusterIP service.
2. Add `LLMClient` abstraction in `strategy_node` — routes to Ollama pod or OpenAI API based on the ConfigMap env var.
3. Add `POST /admin/llm-provider` endpoint for live switching from the UI.
4. Write Kubernetes manifests under `k8s/`: Deployments, Services, StatefulSet, PVCs, ConfigMaps, Secrets, Ingress.
5. Separate `Dockerfile` and `Dockerfile.finbert`.

**Resource requirements for the VM:**

| Pod | RAM |
|---|---|
| postgres | ~256 MB |
| api | ~512 MB |
| finbert | ~1 GB |
| ollama (llama3.2:3b) | ~4 GB |
| k3s system overhead | ~512 MB |
| **Total** | **~6.5 GB** |

Assign at least **10 GB RAM** to the Linux VM; 16 GB recommended.

---

## Step 1.6 — Signal Quality Monitoring (Test Environment Gate)
*Python · PostgreSQL · Grafana · CronJob*

Before promoting to production, measure whether the agent signals actually have predictive value. This step runs on the test environment (Kubernetes cluster) for 2–4 weeks and produces the evidence needed to trust — or distrust — the system.

**The rule:** do not promote to production until rolling DA > 55% and IC > 0.05 over a 30-day window.

---

### Components

#### Prediction Store
Every time `decision_report_node` completes, persist the prediction to a new `predictions` table:

```sql
CREATE TABLE predictions (
    id          SERIAL PRIMARY KEY,
    symbol      TEXT NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL,
    final_action TEXT NOT NULL,          -- BUY / WAIT / AVOID
    confidence  FLOAT NOT NULL,
    entry_zone  TEXT,
    critic_verdict TEXT,
    critic_severity TEXT,
    evaluated   BOOLEAN DEFAULT FALSE
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
| `evaluation-worker` | CronJob (hourly) | Fetch actual prices, score predictions |
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

Every module below targets C++20 or later.

---

#### Module 1 — Indicator Engine (`cpp/indicators/`)
*Replaces `src/agents/tools/indicators.py`*

Compute RSI, EMA, SMA, MACD, Bollinger Bands, ATR, OBV on large price series without the Python GIL.

**C++20 features used:**
- `std::span<const double>` — non-owning view into the caller's price array, zero-copy
- `std::ranges::transform` / `std::views::drop` — functional pipeline over price windows
- **Concepts** (`Arithmetic`, `PriceSeries`) — constrain templates so `compute_rsi<int>` fails at compile time with a readable error
- `std::format` — format output strings without `sprintf`
- `consteval` — compile-time validation of period parameters (period > 0)

```cpp
template <Arithmetic T>
auto compute_rsi(std::span<const T> closes, int period = 14) -> std::vector<double>;
```

---

#### Module 2 — Risk Calculator (`cpp/risk/`)
*Replaces `src/agents/tools/risk.py`*

HHI, VaR (historical simulation), CVaR, Kelly criterion, P&L with weighted average cost basis.

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

---

### C++20 Features Coverage Summary

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

## Summary

| Step | Focus | AI / Tech | Status |
|---|---|---|---|
| 1 | Complete agent pipeline | FinBERT, Ollama LLM, LangGraph | ✅ Done |
| 1.5 | Kubernetes deployment | k3s, Docker, nginx-ingress | 🔲 Next |
| 1.6 | Signal quality monitoring | Prediction store, eval worker, IC/DA/PnL, Grafana | 🔲 Test env gate |
| 2 | ML regime detection | HMM, GMM (scikit-learn / hmmlearn) | 🔲 Planned |
| 3 | C++ engine + ONNX | pybind11, ONNX Runtime | 🔲 Planned |
| 4 | Price forecasting | LSTM / TFT (PyTorch) | 🔲 Planned |
| 5 | Backtesting | Walk-forward, signal attribution | 🔲 Planned |
| 6 | RL position sizing | PPO / SAC (stable-baselines3) | 🔲 Planned |

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
