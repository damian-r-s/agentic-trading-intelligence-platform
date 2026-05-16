# Agentic Trading Intelligence Platform

Production-grade multi-agent AI trading research platform powered by LangGraph, RAG, and vector search.

## Features

- FastAPI backend
- LangGraph orchestration
- Vector search with FAISS
- Retrieval-Augmented Generation (RAG)
- Multi-agent workflows
- Evaluation and observability

## Tech Stack

- Python
- FastAPI
- LangGraph
- FAISS
- OpenAI
- PostgreSQL
- Docker
- Kubernetes

## Project Structure

```text
.
├── DockerFile
├── app.py
├── main.py
├── src/
│   ├── api/
│   ├── core/
│   ├── ingestion/
│   └── retrieval/
├── test/
└── docs/
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

## Binance API

Create a read-only Binance API key with `USER_DATA` access and keep trading and withdrawals disabled.

Copy `.env.example` to `.env` and fill:

```bash
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_BASE_URL=https://api.binance.com
BINANCE_RECV_WINDOW=5000
```

The first portfolio endpoint is:

```bash
GET /portfolio
```

It fetches Spot account balances from Binance and returns a normalized snapshot.

For agent workflows, use:

```bash
GET /portfolio/state
```

It returns current balances, normalized historical BUY/SELL trades for held assets, and current open orders waiting for execution.

To inspect account-specific maker/taker fees:

```bash
GET /trade-fees
GET /trade-fees?symbol=BTCUSDT
```

Binance returns these fees per trading pair. They are useful for estimating the cost of future buy/sell decisions.

## Roadmap

- [x] FastAPI setup
- [x] Query endpoint
- [ ] Document ingestion
- [ ] Embeddings
- [ ] FAISS retrieval
- [ ] Multi-agent workflows
- [ ] Evaluation system
- [ ] Observability
- [ ] Kubernetes deployment
