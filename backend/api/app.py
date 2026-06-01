from fastapi import FastAPI
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

from backend.rag.generator import (
    generate_answer
)

app = FastAPI(
    title="Engineering Knowledge Assistant API"

)
class ChatRequest(BaseModel):

    question: str

@app.get("/")
def root():

    return {
        "message":
        "Engineering Knowledge Base Assistant API"    
        }
@app.get("/health")
def health():

    return {
        "status": "healthy"
    }
@app.post("/chat")
def chat(
    request: ChatRequest
):

    response = generate_answer(
        request.question
    )

    return response
