from backend.database.chroma_manager import (
    collection
)

def retrieve_relevant_chunks(
        query,
        top_k=10
):
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    return results