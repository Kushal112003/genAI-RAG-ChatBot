"""
Chat API Routes
================
Handles real-time chat streaming and conversation history management.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.rag.generator import generate_answer_stream
from backend.rag.memory import clear_history

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    question: str
    provider: str = None  # Optional: LLM provider name
    context_override: str = None


@router.post("/chat")
async def chat(request: ChatRequest):
    """Stream an answer to the user's question using the RAG pipeline."""
    return StreamingResponse(
        generate_answer_stream(
            request.question,
            provider_name=request.provider,
            context_override=request.context_override,
        ),
        media_type="text/event-stream",
    )


@router.delete("/history")
def delete_history():
    """Clear the conversation memory."""
    clear_history()
    return {"message": "History cleared"}
