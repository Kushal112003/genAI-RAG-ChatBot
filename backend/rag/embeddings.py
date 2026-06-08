import uuid
from backend.database.chroma_manager import (
    collection
)


def store_embeddings(chunks):

    for index, chunk in enumerate(chunks):

        collection.add(

            documents=[chunk["text"]],

            metadatas=[chunk["metadata"]],

            ids=[str(uuid.uuid4())]
        )

    print("\nEmbeddings stored successfully.")