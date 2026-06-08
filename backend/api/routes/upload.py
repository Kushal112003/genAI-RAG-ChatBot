"""
Upload API Routes
==================
Handles document upload via REST API with domain tagging.
This makes the backend usable as a standalone API (not just through Streamlit).
"""

import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from backend.ingestion.incremental_ingest import ingest_single_document
from backend.database.chroma_manager import get_collection, client

router = APIRouter(tags=["Upload"])

DATA_DIR = Path("data")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(default="engineering"),
):
    """
    Upload a document and ingest it into the vector database.

    Args:
        file:   The document file (PDF, DOCX, or TXT).
        domain: The document category — 'engineering' or 'policy'.
    """

    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt"}
    suffix = Path(file.filename).suffix.lower()

    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {', '.join(allowed_extensions)}",
        )

    # Validate domain
    if domain not in ("engineering", "policy"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain: {domain}. Must be 'engineering' or 'policy'.",
        )

    # Save the uploaded file
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_path = DATA_DIR / file.filename

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingest into vector database
    try:
        chunk_count = ingest_single_document(str(save_path), domain=domain)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        )

    return {
        "message": f"{file.filename} indexed successfully",
        "filename": file.filename,
        "domain": domain,
        "chunks": chunk_count,
    }


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Selectively delete a document and its chunks from the database.
    """
    file_path = DATA_DIR / filename

    collection = get_collection()
    
    # 1. Soft Delete from ChromaDB to prevent HNSW crash
    try:
        data = collection.get(where={"source": filename}, include=["metadatas"])
        if data["ids"]:
            # Overwrite the chunks with empty text and a 'deleted' domain
            # This hides them from queries without triggering the ChromaDB delete bug
            empty_docs = [""] * len(data["ids"])
            new_metas = [{"source": "deleted", "domain": "deleted"}] * len(data["ids"])
            collection.upsert(ids=data["ids"], documents=empty_docs, metadatas=new_metas)
            chunks_deleted = len(data["ids"])
        else:
            chunks_deleted = 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to soft delete from DB: {str(e)}")

    # 2. Delete the physical file
    file_deleted = False
    if file_path.exists():
        file_path.unlink()
        file_deleted = True

    if not file_deleted and chunks_deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found in database or filesystem.")

    return {
        "message": f"{filename} deleted successfully",
        "chunks_deleted": chunks_deleted,
        "file_deleted": file_deleted
    }


@router.delete("/documents/all/clear")
async def wipe_database():
    """
    Completely wipe the vector database and delete all uploaded files.
    """

    try:
        # Remove entire collection
        client.delete_collection(
            "engineering_knowledge_base"
        )

        # Recreate fresh collection
        from backend.database import chroma_manager

        chroma_manager.collection = (
            client.get_or_create_collection(
                name="engineering_knowledge_base"
            )
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset database: {str(e)}"
        )

    # Delete uploaded files
    files_deleted = 0

    if DATA_DIR.exists():

        for file in DATA_DIR.iterdir():

            if (
                file.is_file()
                and file.name != "telemetry.db"
            ):

                file.unlink()
                files_deleted += 1

    return {
        "message": "Database completely reset",
        "files_deleted": files_deleted
    }