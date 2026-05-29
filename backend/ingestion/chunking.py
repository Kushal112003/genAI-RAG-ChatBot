from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)


def chunk_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = []

    for doc in documents:

        split_texts = splitter.split_text(
            doc["text"]
        )

        for chunk in split_texts:

            chunks.append({
                "text": chunk,
                "metadata": doc["metadata"]
            })

    return chunks