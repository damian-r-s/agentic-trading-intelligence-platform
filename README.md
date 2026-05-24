# Agentic Trading Intelligence Platform

Production-grade multi-agent AI trading research platform. The system prepares trading decisions for human approval — it does not trade autonomously.

Powered by LangGraph, FastAPI, and the Binance API.

## Architecture

```
FastAPI
  └── LangGraph Orchestrator
        ├── Portfolio Agent        — balances, prices, open orders, trade history
        ├── Market Regime Agent    — bull/bear/sideways, risk-on/risk-off
        ├── Market Saturation Agent — overheated sectors, funding rates, fear & greed
        ├── Technical Analysis Agent — RSI, MACD, EMA, support/resistance
        ├── Momentum Agent         — price acceleration, volume spikes, breakouts
        ├── Liquidity Agent        — order book, spread, slippage estimate
        ├── Fundamental Agent      — tokenomics, supply, vesting, ecosystem
        ├── News & Sentiment Agent — news, social sentiment, regulatory events
        ├── Correlation Agent      — diversification impact, BTC/ETH correlation
        ├── Risk Agent             — position size, stop-loss, max allocation
        ├── Strategy Agent         — BUY / WAIT / AVOID + entry zone + thesis
        ├── Critic Agent           — challenges the proposal, flags contradictions
        └── Decision Report Agent  — final report with confidence score
              └── Human Approval   ← YOU decide
```

## Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- LangGraph 1.1 + LangChain
- OpenAI API (LLM backbone)
- FAISS (vector search)
- Binance REST API (read-only)
- Docker

## Project Structure

```
.
├── app.py                        # FastAPI app + router registration
├── main.py                       # Uvicorn entrypoint
├── src/
│   ├── api/
│   │   ├── portfolio.py          # GET /portfolio, /portfolio/state, /trade-fees
│   │   ├── market_data.py        # GET /market-data/{symbol}/candles|order-book|stats
│   │   ├── analyze.py            # GET /agent/analyze
│   │   ├── query.py              # RAG query endpoint
│   │   └── ingestion.py          # PDF ingestion endpoint
│   ├── agents/
│   │   └── tools/
│   │       ├── graph.py          # LangGraph workflow definition
│   │       ├── state.py          # TradingDecisionState (shared agent state)
│   │       ├── risk.py           # Risk metrics calculations
│   │       └── nodes/            # Individual graph nodes
│   ├── exchanges/
│   │   └── binance/
│   │       ├── client.py         # Raw Binance HTTP client (signed + public)
│   │       ├── service.py        # Portfolio normalization service
│   │       └── market_data.py    # OHLCV, order book, 24h stats
│   ├── market_data/
│   │   └── providers.py          # Protocol interfaces for data providers
│   ├── core/
│   │   └── config.py             # Settings (env vars)
│   ├── retrieval/                # FAISS vector store + embeddings
│   └── ingestion/                # PDF loader + chunking
└── test/
```

## Run Locally

```bash
python main.py
```

or:

```bash
uvicorn app:app --reload
```

## Docker

```bash
docker build -f DockerFile -t agentic-trading-intelligence-platform .
docker run -p 8000:8000 agentic-trading-intelligence-platform
```

## Binance API Setup

Create a **read-only** Binance API key with `USER_DATA` access. Keep trading and withdrawals **disabled**.

Copy `.env.example` to `.env`:

```bash
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_BASE_URL=https://api.binance.com
BINANCE_RECV_WINDOW=5000
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
GET /market-data/{symbol}/indicators?interval=4h&limit=500 EMA, SMA, RSI, MACD, Bollinger Bands, ATR, OBV + signals
```

### Agent Workflows

```
GET /agent/analyze?symbol=BTCUSDT  Run portfolio analysis workflow (default: BTCUSDT)
```

### RAG / Knowledge Base

```
POST /ingest                       Ingest a PDF into the vector store
POST /query                        Query the knowledge base with natural language
```

## Risk Metrics

The `/portfolio/state` endpoint computes the following risk metrics automatically:

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
- [x] Milestone 5 — Complete agent pipeline: Strategy, Critic, Report, News & Sentiment (FinBERT), Correlation
- [x] Milestone 6 — Postgreas data base as local cache
- [ ] Milestone 7 — ML regime detection: Hidden Markov Model replacing rule-based market regime node
- [ ] Milestone 8 — C++ engine: indicator + risk calculator via pybind11, ONNX inference bridge
- [ ] Milestone 9 — Price forecasting: LSTM / Temporal Fusion Transformer signal (PyTorch)
- [ ] Milestone 10 — Backtesting: walk-forward validation, signal attribution per agent
- [ ] Milestone 11 — RL execution agent: learned position sizing (PPO/SAC, stable-baselines3)

See [docs/ROADMAP.md](docs/ROADMAP.md) for full context, rationale, and implementation details.
