import chromadb

client = chromadb.PersistentClient(
    path="vectorstore"
)

collection = client.get_or_create_collection(
    name="engineering_knowledge_base"
)

print("Total Chunks:", collection.count())

all_data = collection.get()

deleted_count = 0

for meta in all_data["metadatas"]:
    if meta and meta.get("source") == "deleted":
        deleted_count += 1

print("Deleted Chunks:", deleted_count)
print("Active Chunks:", collection.count() - deleted_count)