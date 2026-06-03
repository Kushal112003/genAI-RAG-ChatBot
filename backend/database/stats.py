from backend.database.chroma_manager import collection


def get_stats():

    data = collection.get()

    return {

        "chunks":
        len(data["ids"]),

        "documents":
        len(
            set(
                meta["source"]
                for meta 
                in data["metadatas"]
            )
        )
    }    
    
