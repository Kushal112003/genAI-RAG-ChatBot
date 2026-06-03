from datasets import Dataset

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
import json
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from dotenv import load_dotenv

load_dotenv()


def run_ragas_evaluation():

    evaluator_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )

    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    data = {
        "question": [
            "What is Terraform?"
        ],

        "answer": [
            """
Terraform is an Infrastructure as Code tool
used to provision and manage infrastructure.
"""
        ],

        "contexts": [
            [
                """
Terraform is an infrastructure provisioning
tool that uses declarative configuration.
"""
            ]
        ],

        "ground_truth": [
            """
Terraform is an Infrastructure as Code
tool used for infrastructure provisioning.
"""
        ]
    }

    dataset = Dataset.from_dict(data)

    results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings
    )

    scores = {
        "faithfulness":
            float(results["faithfulness"]),
        "answer_relevancy":
            float(results["answer_relevancy"]),
        "context_precision":
            float(results["context_precision"]),
        "context_recall":
            float(results["context_recall"]),
    }

    with open(
        "backend/evaluation/results.json",
        "w"
    ) as f:

        json.dump(
            scores,
            f,
            indent=4
        )

    return scores