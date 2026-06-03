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
    file_path
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

    for chunk in chunks:

        collection.add(

            documents=[
                chunk["text"]
            ],

            metadatas=[
                chunk["metadata"]
            ],

            ids=[
                str(uuid.uuid4())
            ]
        )

    return len(chunks)