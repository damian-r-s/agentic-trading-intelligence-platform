from fastapi import FastAPI

from src.api.analyze import router as analyze_router
from src.api.ingestion import router as ingestion_router
from src.api.market_data import router as market_data_router
from src.api.portfolio import router as portfolio_router
from src.api.query import router as query_router

app = FastAPI(
    title="Agentic Trading Intelligence Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(query_router)
app.include_router(ingestion_router)
app.include_router(portfolio_router)
app.include_router(market_data_router)
app.include_router(analyze_router)


@app.get("/")
async def root():
    return {
        "message": "Agentic Trading Intelligence Platform",
        "swagger": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }
