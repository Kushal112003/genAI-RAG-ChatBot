import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb 

client = chromadb.PersistentClient(
    path="vectorstore"
)

collection = client.get_or_create_collection(
    name="engineering_knowledge_base",
)