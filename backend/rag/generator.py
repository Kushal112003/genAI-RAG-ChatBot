import os

from groq import Groq

from backend.rag.retriever import (
    retrieve_relevant_chunks
)

from backend.rag.memory import (
    add_message,
    get_history
)

client = Groq(
    api_key=os.getenv(
        "GROQ_API_KEY"
    )
)


def generate_answer(question):

    # ==========================
    # STORE USER MESSAGE
    # ==========================

    add_message(
        "user",
        question
    )

    history = get_history()

    # ==========================
    # RETRIEVE DOCUMENTS
    # ==========================

    retrieved = retrieve_relevant_chunks(
        question,
        top_k=8
    )

    contexts = []

    sources = []

    for doc, meta in zip(
        retrieved["documents"][0],
        retrieved["metadatas"][0]
    ):

        contexts.append(doc)

        sources.append(
            meta.get(
                "source",
                "Unknown"
            )
        )

    context_text = "\n\n".join(
        contexts
    )

    # ==========================
    # PROMPT
    # ==========================

    prompt = f"""
You are a Senior Cloud Engineer, DevOps Engineer, Platform Engineer and Technical Mentor.

Your job is to answer questions using the uploaded engineering documentation.

========================================
CONVERSATION HISTORY
========================================

{history}

========================================
RETRIEVED DOCUMENTATION
========================================

{context_text}

========================================
CURRENT QUESTION
========================================

{question}

========================================
RULES
========================================

1. Use uploaded documentation as the primary source.

2. Use conversation history to understand follow-up questions.

3. Resolve references such as:
   - it
   - this
   - that
   - alternative
   - compare
   - difference

   using previous conversation context.

4. First answer the user's question directly in 1-3 sentences.

5. Then provide a detailed explanation if needed.

6. Information found in uploaded documents must be placed under:

   "Information From Documents"

7. Information that comes from your own engineering knowledge must be placed under:

   "Additional Engineering Knowledge"

8. Never present LLM knowledge as if it came from uploaded documents.

9. If uploaded documents do not contain enough information, explicitly state:

   "The uploaded documents do not contain enough information to fully answer this question."

10. Keep explanations practical and engineering-focused.

11. Use examples whenever useful.

12. Do not invent document content.

========================================
RESPONSE STYLE
========================================

For simple questions:
- Answer briefly.

For technical questions:
- Direct Answer
- Information From Documents
- Additional Engineering Knowledge
- Example (if relevant)

"""
    # ==========================
    # LLM CALL
    # ==========================

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.3,

        max_tokens=1200
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    # ==========================
    # STORE ASSISTANT RESPONSE
    # ==========================

    add_message(
        "assistant",
        answer
    )

    # ==========================
    # RETURN
    # ==========================

    return {

        "answer": answer,

        "source": list(
            set(sources)
        )
    }