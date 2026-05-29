import chromadb

client = chromadb.PersistentClient(
    path="vectorstore"
)

print("ChromaDB working successfully")