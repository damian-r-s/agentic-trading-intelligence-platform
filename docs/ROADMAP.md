# Roadmap

R&D roadmap for the Agentic Trading Intelligence Platform.

**Goals:**
- Build a sellable AI trading research product (SaaS / startup)
- Introduce a C++ codebase for performance-critical numerical work
- Demonstrate quantitative engineering depth for roles at proprietary trading firms (ICM, Millennium)

---

## Step 1 — Complete the Agent Pipeline
*~2 weeks · Python · LangGraph*

Finish the agents described in the architecture but not yet wired into the graph.

| Agent | Output |
|---|---|
| **Strategy Agent** | BUY / WAIT / AVOID + entry zone + thesis |
| **Critic Agent** | Challenges the proposal, flags contradictions |
| **Decision Report Agent** | Final report with confidence score |
| **News & Sentiment Agent** | News headlines + social sentiment signal |
| **Correlation Agent** | BTC/ETH correlation, portfolio diversification score |

**AI addition:** The News & Sentiment Agent uses a local `sentence-transformers` model (FinBERT) for headline classification — not just an LLM prompt. Embed headlines, score sentiment on a continuous scale, aggregate into a signal. The inference stack (`torch`, `transformers`, CUDA) is already installed.

Completing this step closes the gap between the README architecture diagram and the running code, producing a coherent end-to-end product.

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

Regime models with confidence estimates are a standard topic in quantitative interviews at multi-strategy funds.

---

## Step 3 — C++ Engine + ONNX Integration
*~3 weeks · C++20 · pybind11 · ONNX Runtime*

Introduce a C++ extension that handles all performance-critical numerical work. Python orchestrates agents; C++ handles heavy computation.

**Build system:** CMake 3.28 + `pybind11`. The extension is imported in Python exactly like any other module (`from indicators_cpp import compute_rsi`). This architecture mirrors how production quant systems are structured at trading firms.

**ONNX bridge:** Export the HMM/GMM from Step 2 to ONNX. Run inference from C++ using `onnx-runtime`. Full pipeline: Python trains → ONNX serialises → C++ serves.

---

### C++ Modules Map

Every module below targets C++20 or later. Each entry lists the specific language features it exercises — this is the skills matrix for the quant developer portfolio.

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
- **Coroutines (`co_await`, `co_yield`)** — async I/O without callbacks; models how modern async networking code is written at HFT firms
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

Frame this as *one signal among many* — the analysis agent weighs it alongside technical, regime, and sentiment signals. This is intellectually honest and is exactly how ML signals are used at quant funds: as features, not oracles.

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

This is the frontier piece that differentiates the platform from classical quant systems. RL for execution and position sizing is an active research area at top-tier trading firms. It is publishable as a research paper and forms a strong narrative for a startup pitch: *"AI that learns optimal position sizing from market microstructure."*

---

## Summary

| Step | Focus | AI / Tech | C++20 Highlight | Target Audience |
|---|---|---|---|---|
| 1 | Complete agent pipeline | FinBERT sentiment | — | Working product |
| 2 | ML regime detection | HMM, GMM | — | Quant interviews |
| 3 | C++ engine + ONNX | pybind11, ONNX Runtime | Concepts, spans, ranges, coroutines, jthread | Quant portfolio, low-latency |
| 4 | Price forecasting | LSTM / TFT (PyTorch) | — | ML alpha research |
| 5 | Backtesting | Walk-forward, signal attribution | Coroutines, variant/visit, mdspan | Risk management, R&D |
| 6 | RL position sizing | PPO / SAC (stable-baselines3) | — | Frontier R&D, startup pitch |

**C++ modules inside Step 3:**

| Module | Replaces | Key C++20 features |
|---|---|---|
| `cpp/indicators/` | `indicators.py` | Concepts, `std::span`, `std::ranges`, `consteval` |
| `cpp/risk/` | `risk.py` | Concepts, designated initializers, `std::ranges` |
| `cpp/orderbook/` | inline liquidity compute | `std::span`, `<=>`, `std::atomic_ref` |
| `cpp/feed/` | Python WebSocket (new) | Coroutines, `std::jthread`, `std::stop_token`, `std::barrier` |
| `cpp/backtest/` | Python backtester (new) | `std::generator`, Concepts, `std::variant`, `std::visit` |
| `cpp/stats/` | inline stats (new) | Concepts, `std::ranges`, `std::latch`, `consteval` |

Steps 2 and 6 carry the most weight for quantitative developer roles at proprietary trading firms.
Steps 1, 4, 5, and 6 together form the core of a fundable AI trading research startup.
The C++ modules in Step 3 demonstrate proficiency in all major C++20 features and mirror production quant infrastructure.
