"""
Hybrid Search (BM25 + Semantic)
================================
Combines keyword-based BM25 retrieval with ChromaDB's vector
similarity search using Reciprocal Rank Fusion (RRF).

This dramatically improves retrieval for exact keyword matches
(e.g., "kubectl", "PTO policy") while preserving semantic understanding.
"""

import re
import math
from collections import defaultdict

from backend.database.chroma_manager import get_collection

def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\w+", text.lower())


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    avg_dl: float,
    doc_freq: dict,
    n_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Compute BM25 score for a single document."""
    dl = len(doc_tokens)
    score = 0.0

    for qt in query_tokens:
        if qt not in doc_freq:
            continue

        tf = doc_tokens.count(qt)
        df = doc_freq[qt]
        idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
        score += idf * tf_norm

    return score


def _reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[str]:
    """
    Merge multiple ranked lists using RRF.
    Each list is a list of document IDs ordered by relevance.
    Returns a single list of IDs sorted by fused score (descending).
    """
    scores = defaultdict(float)

    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] += 1.0 / (k + rank)

    return sorted(scores, key=scores.get, reverse=True)


def hybrid_retrieve(
    query: str,
    top_k: int = 5,
    domain: str = None,
) -> dict:
    """
    Perform hybrid retrieval: BM25 + semantic vector search,
    merged via Reciprocal Rank Fusion.

    Args:
        query:  The user's question.
        top_k:  Number of final results to return.
        domain: Optional domain filter ('engineering' or 'policy').

    Returns:
        dict with keys 'documents', 'metadatas', 'ids' (same shape as ChromaDB).
    """

    # ── 1. Fetch all candidate documents from ChromaDB ──────
    get_params = {"include": ["documents", "metadatas"]}
    if domain:
        get_params["where"] = {"domain": domain}

    all_data = get_collection().get(**get_params)

    if not all_data["ids"]:
        # No documents — return empty result in ChromaDB format
        return {"documents": [[]], "metadatas": [[]], "ids": [[]]}

    doc_ids = []
    doc_texts = []
    doc_metas = []

    for doc_id, doc_text, meta in zip(
        all_data["ids"],
        all_data["documents"],
        all_data["metadatas"]
        ):
        if (
            meta.get("deleted", False)
            or meta.get("domain") == "deleted"
            or meta.get("source") == "deleted"
            ):
            continue
        
        doc_ids.append(doc_id)
        doc_texts.append(doc_text)
        doc_metas.append(meta)
        
        if not doc_ids:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "ids": [[]]
                }

    # ── 2. BM25 ranking ─────────────────────────────────────
    query_tokens = _tokenize(query)
    all_doc_tokens = [_tokenize(doc) for doc in doc_texts]
    avg_dl = sum(len(t) for t in all_doc_tokens) / max(len(all_doc_tokens), 1)

    # Document frequency
    doc_freq = defaultdict(int)
    for tokens in all_doc_tokens:
        seen = set(tokens)
        for t in seen:
            doc_freq[t] += 1

    bm25_scores = []
    for i, tokens in enumerate(all_doc_tokens):
        score = _bm25_score(
            query_tokens, tokens, avg_dl, doc_freq, len(doc_ids)
        )
        bm25_scores.append((doc_ids[i], score))

    bm25_ranked = [
        doc_id
        for doc_id, _ in sorted(bm25_scores, key=lambda x: x[1], reverse=True)
    ]

    # ── 3. Semantic (vector) ranking ────────────────────────
    query_params = {"query_texts": [query], "n_results": min(top_k * 3, len(doc_ids)), "where": {
        "deleted": {"$ne": True}}
    }
    if domain:
        query_params["where"] = {
        "$and": [
            {"deleted": {"$ne": True}},
            {"domain": domain}
        ]
    }
    vector_results = get_collection().query(**query_params)
    vector_ranked = vector_results["ids"][0]

    # ── 4. Reciprocal Rank Fusion ───────────────────────────
    fused_ids = _reciprocal_rank_fusion([bm25_ranked, vector_ranked])[:top_k]

    # ── 5. Assemble final results ───────────────────────────
    id_to_idx = {doc_id: i for i, doc_id in enumerate(doc_ids)}

    final_docs = []
    final_metas = []
    final_ids = []

    for doc_id in fused_ids:
        if doc_id in id_to_idx:
            idx = id_to_idx[doc_id]
            final_docs.append(doc_texts[idx])
            final_metas.append(doc_metas[idx])
            final_ids.append(doc_id)

    return {
        "documents": [final_docs],
        "metadatas": [final_metas],
        "ids": [final_ids],
    }
