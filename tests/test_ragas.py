from backend.evaluation.ragas_eval import (
    run_ragas_evaluation
)

print("Starting RAGAS Test...\n")

results = run_ragas_evaluation()

print("\nRAGAS RESULTS:")
print(results)