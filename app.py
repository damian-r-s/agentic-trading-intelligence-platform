from fastapi import FastAPI

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

app.mount("/ui", StaticFiles(directory="src/ui", html=True), name="ui")

app.include_router(query_router)
app.include_router(ingestion_router)
app.include_router(portfolio_router)
app.include_router(market_data_router)
app.include_router(analyze_router)

@app.get("/")
async def root():
    return FileResponse("src/ui/index.html")