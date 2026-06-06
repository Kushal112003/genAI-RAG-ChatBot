import hashlib
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

def chunk_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    chunks = []
    for doc in documents:

        split_texts = splitter.split_text(
            doc["text"]
        )
        for chunk in split_texts:
            # Generate a deterministic hash ID based on source and text
            source = doc["metadata"].get("source", "unknown")
            hash_input = f"{source}::{chunk}".encode("utf-8")
            chunk_id = hashlib.md5(hash_input).hexdigest()
            
            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": doc["metadata"],
                }
            )
    return chunks