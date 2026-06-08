# tests/test_query.py

from backend.database.chroma_manager import get_collection

collection = get_collection()

result = collection.query(
    query_texts=["terraform"],
    n_results=1
)

print(result)