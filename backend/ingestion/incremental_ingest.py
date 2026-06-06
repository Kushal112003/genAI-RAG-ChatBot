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

import uuid


def ingest_single_document(
    file_path,
    domain="engineering"
):

    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":

        documents = load_pdf(file_path)

    elif suffix == ".docx":

        documents = load_docx(file_path)

    elif suffix == ".txt":

        documents = load_txt(file_path)

    else:

        raise Exception(
            "Unsupported file type"
        )

    chunks = chunk_documents(
        documents
    )

    filename = Path(file_path).name

    texts = []
    metas = []
    ids = []

    for chunk in chunks:
        chunk["metadata"]["domain"] = domain
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

    return len(chunks)