from fastapi import APIRouter, UploadFile, File

from app.ingestion.pdf_loader import extract_text
from app.ingestion.chunking import chunk_text
from app.retrieval.embeddings import embed_texts
from app.core.store import vector_store

router = APIRouter()


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