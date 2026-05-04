from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
async def query(request: QueryRequest):
    return {
        "question": request.question,
        "answer": "Placeholder response"
    }