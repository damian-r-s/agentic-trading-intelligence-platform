from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    content = await file.read()

    return {
        "filename": file.filename,
        "size": len(content),
        "status": "received"
    }