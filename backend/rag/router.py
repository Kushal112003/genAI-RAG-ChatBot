"""
Query Router (Intent Classifier)
==================================
Classifies user questions into document domains so the retriever
can filter by the correct category.

Domains:
  - 'engineering'  — technical / DevOps / cloud topics
  - 'policy'       — company policies, HR, leave, conduct, etc.
"""

from backend.rag.llm_providers import create_llm_client


# Default provider for routing (should be fast + cheap)
DEFAULT_ROUTER_PROVIDER = "Groq (LLaMA 3.1 8B)"


async def classify_intent(
    question: str,
    provider_name: str = None,
) -> str:
    """
    Classify a user question into a document domain.

    Uses a single-token LLM call for speed.
    Returns 'engineering' or 'policy'.
    """

    provider_name = provider_name or DEFAULT_ROUTER_PROVIDER

    try:
        client, model = await create_llm_client(provider_name)
    except ValueError:
        # If provider key is missing, default to engineering
        return "engineering"

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a classification assistant. "
                        "Given a user question, reply with EXACTLY one word: "
                        "'engineering' if the question is about technical topics "
                        "(cloud, DevOps, programming, infrastructure, tools, etc.) "
                        "or 'policy' if the question is about company policies, "
                        "HR rules, leave, conduct, benefits, compliance, etc. "
                        "Reply with ONLY that single word, nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            temperature=0.0,
            max_tokens=5,
        )

        raw = response.choices[0].message.content.strip().lower()

        if "policy" in raw:
            return "policy"
        return "engineering"

    except Exception:
        # On any error, default to engineering
        return "engineering"
