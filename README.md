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
