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

DATA_FOLDER = Path("data")

documents = []

for file in DATA_FOLDER.iterdir():

    suffix = file.suffix.lower()

    if suffix == ".pdf":

        documents.extend(
            load_pdf(str(file))
        )

    elif suffix == ".docx":

        documents.extend(
            load_docx(str(file))
        )

    elif suffix == ".txt":

        documents.extend(
            load_txt(str(file))
        )

print(
    f"\nLoaded {len(documents)} document(s)"
)

chunks = chunk_documents(
    documents
)

print(
    f"Generated {len(chunks)} chunk(s)"
)

try:

    collection.delete(
        ids=collection.get()["ids"]
    )

except:

    pass

for idx, chunk in enumerate(chunks):

    collection.add(
        documents=[chunk["text"]],
        metadatas=[chunk["metadata"]],
        ids=[f"chunk_{idx}"],
    )

print(
    "\nEmbeddings stored successfully."
)