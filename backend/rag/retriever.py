from backend.database.chroma_manager import get_collection

def retrieve_relevant_chunks(
        query,
        top_k=10,
        domain=None
):
    """
    Query ChromaDB for the most relevant chunks.

    If a domain is provided, only chunks tagged with that domain
    will be searched (metadata filtering).
    """

    query_params = {
        "query_texts": [query],
        "n_results": top_k,
    }

    if domain:
        query_params["where"] = {"domain": domain}

    results = get_collection().query(**query_params)

    return results