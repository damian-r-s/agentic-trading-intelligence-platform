from fastapi import APIRouter, UploadFile, File
from fastapi import Depends
from src.api.auth import get_current_user

from src.ingestion.pdf_loader import extract_text
from src.ingestion.chunking import chunk_text
from src.retrieval.embeddings import embed_texts
from src.core.store import vector_store

router = APIRouter(tags=["ingestion"], dependencies=[Depends(get_current_user)])

@router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    file_bytes = await file.read()

    text = extract_text(file_bytes)

    chunks = chunk_text(text)

    embeddings = embed_texts(chunks)

    vector_store.add(embeddings, chunks)

    return {
        "chunks": len(chunks),
        "status": "indexed"
    }
