"""
Analytics API Routes
=====================
Provides system statistics, document inventory, and evaluation triggers.
"""

from fastapi import APIRouter, HTTPException
from backend.database.chroma_manager import get_collection
from backend.database.stats import get_stats
from backend.evaluation.metrics import get_metrics
from backend.rag.llm_providers import get_available_providers, get_all_provider_names
from backend.database.telemetry import get_telemetry_stats, log_feedback
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class FeedbackRequest(BaseModel):
    query_id: int
    feedback_type: str


@router.get("/telemetry")
def telemetry():
    """Return usage analytics from the SQLite telemetry database."""
    return get_telemetry_stats()


@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    """Log user feedback (thumbs up/down) for a specific query."""
    if request.feedback_type not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Invalid feedback type")
    log_feedback(request.query_id, request.feedback_type)
    return {"message": "Feedback recorded"}


@router.get("/stats")
def stats():
    """
    Return high-level system statistics:
    document count, chunk count, and domain breakdown.
    """
    base_stats = get_stats()

    # Domain breakdown
    collection = get_collection()
    data = collection.get(include=["metadatas"])
    domain_counts = {}
    for meta in data["metadatas"]:
        d = meta.get("domain", "untagged")
        domain_counts[d] = domain_counts.get(d, 0) + 1

    base_stats["domains"] = domain_counts
    return base_stats


@router.get("/documents")
def list_documents():
    """
    Return a list of all indexed documents with their domain tags.
    """
    collection = get_collection()

    data = collection.get(include=["metadatas"])

    documents = {}
    for meta in data["metadatas"]:
        source = meta.get("source", "Unknown")
        domain = meta.get("domain", "untagged")

        if source not in documents:
            documents[source] = {
                "filename": source,
                "domain": domain,
                "chunk_count": 0,
            }
        documents[source]["chunk_count"] += 1

    return {"documents": list(documents.values())}


@router.get("/evaluation")
def evaluation_results():
    """Return the latest RAGAS evaluation scores."""
    return get_metrics()


@router.get("/providers")
def list_providers():
    """
    Return all registered LLM providers and which ones have valid keys.
    """
    all_names = get_all_provider_names()
    available = get_available_providers()

    return {
        "providers": [
            {
                "name": name,
                "available": name in available,
            }
            for name in all_names
        ]
    }
