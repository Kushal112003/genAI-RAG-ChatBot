from ragas.dataset_schema import EvaluationDataset, SingleTurnSample

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
import json
import asyncio
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from dotenv import load_dotenv

from backend.rag.generator import generate_answer_stream

load_dotenv()

async def get_answer_and_context(question):
    answer = ""
    contexts = []
    async for chunk in generate_answer_stream(question):
        data = json.loads(chunk)
        if data["type"] == "token":
            answer += data["content"]
        elif data["type"] == "sources":
            contexts = data.get("contexts", [])
    return answer, contexts

def run_ragas_evaluation():

    evaluator_llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0
    )

    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    dataset_path = Path("backend/evaluation/golden_dataset.json")
    with open(dataset_path, "r") as f:
        golden_data = json.load(f)

    samples = []
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    import time
    for item in golden_data:
        question = item["question"]
        ground_truth = item["ground_truth"]
        
        answer, contexts = loop.run_until_complete(get_answer_and_context(question))
        time.sleep(2)  # Delay to respect rate limits
        
        if not contexts:
            contexts = ["No context retrieved."]
            
        sample = SingleTurnSample(
            user_input=question,
            response=answer,
            retrieved_contexts=contexts,
            reference=ground_truth
        )
        samples.append(sample)

    dataset = EvaluationDataset(samples=samples)

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

    def safe_float(val):
        if isinstance(val, list):
            valid_vals = [v for v in val if v is not None and str(v).lower() != 'nan']
            return float(sum(valid_vals) / len(valid_vals)) if valid_vals else 0.0
        return float(val)

    scores = {
        "faithfulness": safe_float(results["faithfulness"]),
        "answer_relevancy": safe_float(results["answer_relevancy"]),
        "context_precision": safe_float(results["context_precision"]),
        "context_recall": safe_float(results["context_recall"]),
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