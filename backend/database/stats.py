from backend.database.chroma_manager import client

def get_stats():

    collection = client.get_or_create_collection(
        name="engineering_knowledge_base"
    )

    data = collection.get()

    return {
        "chunks": len(data["ids"]),
        "documents": len(
            set(
                meta["source"]
                for meta in data["metadatas"]
            )
        )
    }