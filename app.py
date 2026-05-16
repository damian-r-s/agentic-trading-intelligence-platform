from fastapi import FastAPI

from src.api.ingestion import router as ingestion_router
from src.api.query import router as query_router

app = FastAPI(
    title="Agentic Trading Intelligence Platform",
    version="0.1.0"
)

app.include_router(query_router)
app.include_router(ingestion_router)


@app.get("/")
async def root():
    return {
        "message": "Agentic Trading Intelligence Platform"
    }
