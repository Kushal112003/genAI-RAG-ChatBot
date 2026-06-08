import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb

client = chromadb.PersistentClient(
    path="vectorstore"
)

def get_collection():
    return client.get_or_create_collection(
        name="engineering_knowledge_base"
    )

collection = get_collection()