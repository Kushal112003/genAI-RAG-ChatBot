import chromadb 

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)

embedding_function = (
    SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2",
    )

)
client = chromadb.PersistentClient(
    path="vectorstore"
)

collection = client.get_or_create_collection(
    name="engineering_knowledge_base",
    embedding_function=embedding_function,
)