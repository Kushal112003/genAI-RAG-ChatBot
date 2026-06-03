from backend.evaluation.ragas_eval import (
    run_ragas_evaluation
)

import json


def get_metrics():

    try:

        with open(
            "backend/evaluation/results.json",
            "r"
        ) as f:

            return json.load(f)

    except:

        return {
            "faithfulness": 0,
            "answer_relevancy": 0,
            "context_precision": 0,
            "context_recall": 0,
        }