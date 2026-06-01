import os

from groq import Groq
from pydantic_settings import sources

from backend.rag.retriever import (
    retrieve_relevant_chunks
)

client = Groq(
    api_key=os.getenv(
        "GROQ_API_KEY"
    )
)

def generate_answer(question):

    retrieved = retrieve_relevant_chunks(
        question,
        top_k=5
    )

    contexts = []
    
    source = []

    for doc, meta in zip(
        retrieved["documents"][0],
        retrieved["metadatas"][0]
    ):
        
        contexts.append(doc)

        source.append(
            meta.get(
                "source",
                "Unknown"
            )
        )

    context_text = "\n\n".join(
        contexts
    )

    prompt = f"""
You are an Engineering Knowledge Assistant.

Answer ONLY using the provided context.

If information is unavailable,
say so clearly.

CONTEXT:

{context_text}

QUESTION:

{question}
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "answer":
            response.choices[0]
            .message.content,

        "source":
            list(set(source))
    }