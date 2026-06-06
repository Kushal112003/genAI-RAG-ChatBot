from dotenv import load_dotenv

load_dotenv()

from backend.rag.generator import (
    generate_answer
)

response = generate_answer(
    "which command in linux is used to change user permissions?"
)

print("\nANSWER:\n")

print(
    response["answer"]
)

print("\nSOURCES:\n")

for source in response["source"]:

    print(source)