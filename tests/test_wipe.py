from backend.database.chroma_manager import collection

print("Count:", collection.count())

ids = collection.get()["ids"]

print("IDs Retrieved:", len(ids))