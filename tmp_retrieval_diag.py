import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

from research_rag.hybrid.config import HybridRAGSettings
from research_rag.hybrid.orchestrator import HybridRAGSystem


def main() -> None:
    cases = json.loads(Path("data/eval/research_eval_suite.json").read_text())[:12]
    system = HybridRAGSystem(HybridRAGSettings.from_env())

    rows = []
    for case in cases:
        question = case["question"]
        result = system.query(question=question, paper_ids=case.get("paper_ids"))
        if float(result.retrieval_quality) < 0.5:
            chunks = result.diagnostic.get("retrieved_chunks", [])[:5]
            rows.append(
                {
                    "question": question,
                    "retrieval_quality": float(result.retrieval_quality),
                    "retries": result.retries,
                    "top_sections": [chunk.get("section") for chunk in chunks],
                    "top_rrf": [round(float(chunk.get("rrf_score", 0.0)), 4) for chunk in chunks],
                    "answer": result.answer[:220].replace("\n", " "),
                }
            )

    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
