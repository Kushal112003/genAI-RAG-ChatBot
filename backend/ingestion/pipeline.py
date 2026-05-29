from backend.ingestion.loaders import (
    load_txt,
    load_pdf,
    load_docx
)

from backend.ingestion.chunking import (
    chunk_documents
)

from backend.rag.embeddings import (
    store_embeddings
)


all_documents = []

all_documents.extend(
    load_txt("data/sample.txt")
)

all_documents.extend(
    load_pdf("data/Pulumi Assignment.pdf")
)

all_documents.extend(
    load_docx("data/GenAI assignment week 1.docx")
)


chunks = chunk_documents(all_documents)


print(f"\nLoaded {len(all_documents)} document(s)")

print(f"Generated {len(chunks)} chunk(s)\n")


store_embeddings(chunks)