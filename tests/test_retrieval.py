from backend.rag.retriever import (
    retrieve_relevant_chunks
)


query = "What is maternity leave policy?"


results = retrieve_relevant_chunks(query)


print("\nRETRIEVAL RESULTS:\n")


documents = results["documents"][0]

metadatas = results["metadatas"][0]


for i in range(len(documents)):

    print(f"\nRESULT {i+1}\n")

    print(documents[i])

    print("\nMETADATA:")

    print(metadatas[i])

    print("\n" + "="*50)