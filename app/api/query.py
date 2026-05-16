from fastapi import APIRouter
from pydantic import BaseModel

from app.core.store import vector_store
from app.retrieval.embeddings import embed_texts

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
async def query(request: QueryRequest):
    question_embedding = embed_texts([request.question])[0]
    chunks = vector_store.search(question_embedding)

    return {
        "question": request.question,
        "chunks": chunks
    }
