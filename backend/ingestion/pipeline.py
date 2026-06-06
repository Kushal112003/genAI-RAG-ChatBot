"""
Full Ingestion Pipeline
========================
Rebuilds the entire vector database from all files in the data/ directory.
Supports domain tagging (defaults to 'engineering' for bulk rebuild).
"""

import uuid
from pathlib import Path

from backend.ingestion.loaders import (
    load_pdf,
    load_docx,
    load_txt,
)

from backend.ingestion.chunking import (
    chunk_documents,
)

from backend.database.chroma_manager import (
    collection,
)


def run_pipeline():
    """
    Load all documents from data/, chunk them, and store in ChromaDB.
    Clears existing data before rebuilding.
    """

    DATA_FOLDER = Path("data")

    if not DATA_FOLDER.exists():
        print("No data/ folder found. Nothing to ingest.")
        return

    documents = []

    for file in DATA_FOLDER.iterdir():

        suffix = file.suffix.lower()

        if suffix == ".pdf":
            documents.extend(load_pdf(str(file)))

        elif suffix == ".docx":
            documents.extend(load_docx(str(file)))

        elif suffix == ".txt":
            documents.extend(load_txt(str(file)))

    print(f"\nLoaded {len(documents)} document(s)")

    chunks = chunk_documents(documents)

    print(f"Generated {len(chunks)} chunk(s)")

    # Clear existing data
    try:
        existing = collection.get()["ids"]
        if existing:
            collection.delete(ids=existing)
            print(f"Cleared {len(existing)} existing chunks")
    except Exception:
        pass

    # Store with intelligent domain tagging
    texts = []
    metas = []
    ids = []
    
    for chunk in chunks:
        # Determine domain dynamically based on filename
        source_name = chunk["metadata"].get("source", "")
        if "policy" in source_name.lower():
            chunk_domain = "policy"
        else:
            chunk_domain = "engineering"
            
        chunk["metadata"]["domain"] = chunk_domain
        texts.append(chunk["text"])
        metas.append(chunk["metadata"])
        ids.append(chunk["id"])
        
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        collection.upsert(
            documents=texts[i:i+batch_size],
            metadatas=metas[i:i+batch_size],
            ids=ids[i:i+batch_size],
        )

    print("\nEmbeddings stored successfully.")
    print(f"Total chunks in database: {collection.count()}")


if __name__ == "__main__":
    run_pipeline()