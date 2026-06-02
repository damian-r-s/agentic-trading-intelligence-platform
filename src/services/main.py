import uvicorn
from fastapi import FastAPI
from src.services.finbert_api import router

app = FastAPI(title="FinBERT Sentiment Service")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8001)