from backend.database.chroma_manager import get_collection

collection = get_collection()

data = collection.get(
    where={"source": "Terraform.pdf"},
    include=["metadatas"]
)

print("Terraform Chunks:", len(data["ids"]))

if data["metadatas"]:
    print(data["metadatas"][0])