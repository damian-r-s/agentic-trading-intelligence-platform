from fastapi import APIRouter
from pydantic import BaseModel

from src.core.store import vector_store
from src.retrieval.embeddings import embed_texts

router = APIRouter(tags=["rag"])


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
