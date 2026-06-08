"""
RAG Answer Generator (Streaming)
=================================
Generates answers using retrieved document context and conversation history.
Supports multiple LLM providers via the provider registry.
Enforces strict citation parsing so only actually-referenced sources appear.
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

from backend.rag.hybrid_search import hybrid_retrieve
from backend.rag.memory import add_message, get_history
from backend.rag.router import classify_intent
from backend.rag.llm_providers import create_llm_client
from backend.database.telemetry import log_query
import time


# Default provider — can be overridden per-request from the frontend
DEFAULT_PROVIDER = "Groq (LLaMA 3.1 8B)"


async def generate_answer_stream(question: str, provider_name: str = None, context_override: str = None):
    """
    Async generator that streams the LLM response token-by-token.

    Args:
        question:      The user's question.
        provider_name: Which LLM provider to use (from llm_providers registry).
                       Falls back to DEFAULT_PROVIDER if not specified.

    Yields:
        JSON-encoded lines with type "token", "sources", or "error".
    """

    provider_name = provider_name or DEFAULT_PROVIDER
    start_time = time.time()

    # ── Get LLM client ──────────────────────────
    try:
        client, model = await create_llm_client(provider_name)
    except ValueError as e:
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"
        return

    # ── Store user message ──────────────────────
    add_message("user", question)
    history = get_history()

    # ── Route query to domain ───────────────────
    if context_override == "Engineering Knowledge Base":
        domain = "engineering"
    elif context_override == "Company Policy":
        domain = "policy"
    else:
        domain = await classify_intent(question, provider_name)

    # ── Retrieve documents (Hybrid Search, Top 6) ──────────────────────
    retrieved = hybrid_retrieve(question, top_k=6, domain=domain)

    if not retrieved["documents"][0]:
        msg = (
            "I cannot answer this question because "
            "the provided documents do not contain "
            "relevant information."
            )
        yield json.dumps({
            "type": "token",
            "content": msg
        }) + "\n"
        
        yield json.dumps({
            "type": "sources",
            "content": [],
            "contexts": [],
            "domain": domain,
            "query_id": None,
            "latency_ms": 0
        }) + "\n"
        
        return

    contexts = []
    sources = []
    source_map = {}

    for idx, (doc, meta) in enumerate(
        zip(retrieved["documents"][0], retrieved["metadatas"][0])
    ):
        source_name = meta.get("source", "Unknown")
        page_num = meta.get("page", None)
        
        if page_num:
            full_source_name = f"{source_name} (Page {page_num})"
        else:
            full_source_name = source_name
            
        source_label = f"[Source {idx + 1}: {full_source_name}]"
        contexts.append(f"{source_label}\n{doc}")
        sources.append(full_source_name)
        source_map[source_label] = full_source_name

    context_text = "\n\n".join(contexts)

    # ── Build prompt ────────────────────────────
    if domain == "policy":
        persona_and_instructions = """You are an HR and Corporate Policy Expert.
Your primary role is to answer employee inquiries accurately and professionally using ONLY the provided company policy documentation. 
If a user asks about engineering, coding, or technical topics, politely inform them that you are the HR assistant and ask them to switch to the Engineering Knowledge Base."""
    else:
        persona_and_instructions = """You are a Principal Cloud Architect, DevOps Specialist, and Technical Mentor.
Your primary role is to answer complex technical questions accurately and professionally using ONLY the uploaded engineering documentation.
If a user asks about HR policies, leave, or corporate conduct, politely inform them that you are a technical assistant and ask them to switch to the Company Policy database."""

    prompt = f"""
{persona_and_instructions}

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
RULES FOR ANSWERING
========================================

1. **Strict Context:** Rely primarily on the "RETRIEVED DOCUMENTATION". Do not hallucinate or invent policies/technical details.
2. **Context Resolution:** Use the "CONVERSATION HISTORY" to resolve pronouns (e.g., "it", "this", "that") and understand follow-up questions.
3. **Format & Professionalism:**
   - Use high-quality, professional Markdown formatting.
   - Use clear **Headers** (e.g., `### Overview`, `### Details`).
   - Use **Bullet Points** and **Numbered Lists** to break down complex information.
   - Use **Tables** where comparing items or listing structured data is beneficial.
   - Use **Bold** text to highlight key terms.
4. **Structure:**
   - Start with a direct, concise 1-3 sentence summary.
   - Follow with a structured, detailed explanation.
   - If applicable, provide practical examples.
5. **Transparency & Strict Guardrails (CRITICAL):**
    - If the provided documents do not contain the answer, YOU MUST explicitly state: "I cannot answer this question because the provided documents do not contain relevant information."
    - DO NOT use your internal training data or general knowledge to answer. 
    - DO NOT provide any general explanations if the answer is missing from the context.
6. **Citation Requirement (CRITICAL):**
   - At the absolute end of your response, you MUST include a line starting with "SOURCES_USED:" followed by a comma-separated list of ONLY the source labels you referenced.
   - Example: `SOURCES_USED: [Source 1: Terraform.pdf], [Source 3: Employee_Handbook.pdf]`
   - If no sources were used, write: `SOURCES_USED: NONE`
"""

    # ── LLM call (streaming) ────────────────────
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200,
            stream=True,
        )
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            yield json.dumps({
                "type": "error",
                "content": "⚠️ Rate limit reached. Please wait a moment and try again."
            }) + "\n"
        else:
            yield json.dumps({
                "type": "error",
                "content": f"LLM Error: {error_msg}"
            }) + "\n"
        return

    full_answer = ""

    async for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            full_answer += content
            yield json.dumps({"type": "token", "content": content}) + "\n"

    # ── Store assistant response ────────────────
    add_message("assistant", full_answer)

    # ── Parse cited sources ─────────────────────
    cited_sources = []

    if "SOURCES_USED:" in full_answer:
        sources_line = full_answer.split("SOURCES_USED:")[-1].strip()
        if sources_line.upper() != "NONE":
            for label, name in source_map.items():
                if name.lower() in sources_line.lower() or label.lower() in sources_line.lower():
                    cited_sources.append(name)

    # Fallback: if the LLM didn't follow citation format, use all sources
    if not cited_sources and contexts:
        cited_sources = []
    # ── Log Telemetry ───────────────────────────
    duration_ms = int((time.time() - start_time) * 1000)
    query_id = log_query(question, domain, duration_ms, provider_name)

    # ── Yield final sources ─────────────────────
    yield json.dumps({
        "type": "sources",
        "content": list(set(cited_sources)),
        "contexts": [c.split("\n", 1)[-1] for c in contexts],
        "domain": domain,
        "query_id": query_id,
        "latency_ms": duration_ms
    }) + "\n"