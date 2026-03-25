import json
from pathlib import Path
from statistics import mean
import sys

sys.path.insert(0, str(Path("src").resolve()))

from research_rag.hybrid.config import HybridRAGSettings
from research_rag.hybrid.orchestrator import HybridRAGSystem


def main() -> None:
    settings = HybridRAGSettings.from_env()
    system = HybridRAGSystem(settings)

    papers = system.metadata_store.list_papers()
    chunk_counts = [paper.chunk_count for paper in papers]
    all_chunks = system.metadata_store.fetch_chunks(paper_ids=[paper.paper_id for paper in papers])
    empty_chunks = sum(1 for chunk in all_chunks if not (chunk.text or "").strip())
    short_30 = sum(1 for chunk in all_chunks if len((chunk.text or "").strip()) < 30)
    short_80 = sum(1 for chunk in all_chunks if len((chunk.text or "").strip()) < 80)
    print(
        json.dumps(
            {
                "index": {
                    "papers": len(papers),
                    "total_chunks": sum(chunk_counts) if chunk_counts else 0,
                    "avg_chunks_per_paper": round(sum(chunk_counts) / len(chunk_counts), 2) if chunk_counts else 0,
                    "empty_chunks": empty_chunks,
                    "chunks_lt_30_chars": short_30,
                    "chunks_lt_80_chars": short_80,
                }
            },
            indent=2,
        )
    )

    cases = json.loads(Path("data/eval/research_eval_suite.json").read_text())
    eval_rows: list[dict[str, object]] = []
    for case in cases:
        question = case["question"]
        result = system.query(question=question, paper_ids=case.get("paper_ids"))
        eval_rows.append(
            {
                "question": question,
                "rq": float(result.retrieval_quality),
                "retries": int(result.retries),
                "chunks": len(result.citations or []),
                "answer_head": (result.answer or "")[:140].replace("\n", " "),
            }
        )

    eval_rqs = [float(row["rq"]) for row in eval_rows]
    print(
        json.dumps(
            {
                "eval_set": {
                    "count": len(eval_rows),
                    "avg_rq": round(mean(eval_rqs), 4),
                    "min_rq": round(min(eval_rqs), 4),
                    "max_rq": round(max(eval_rqs), 4),
                    "lt_0_4": sum(1 for value in eval_rqs if value < 0.4),
                    "lt_0_5": sum(1 for value in eval_rqs if value < 0.5),
                    "gte_0_7": sum(1 for value in eval_rqs if value >= 0.7),
                }
            },
            indent=2,
        )
    )

    custom_questions = [
        "Summarize the core method in 3 bullet points.",
        "Which experiments directly support the main claim?",
        "What baselines are compared and what are the deltas?",
        "List all datasets and splits mentioned in the paper.",
        "What failure modes or limitations are acknowledged?",
        "What are the strongest quantitative results and on which benchmark?",
        "What ablations isolate component contributions?",
        "What practical deployment constraints are discussed?",
        "How strong is the citation grounding for the final answer?",
        "What is the one-sentence takeaway for a researcher?",
    ]

    print("CUSTOM_RESULTS")
    for question in custom_questions:
        result = system.query(question=question)
        print(
            json.dumps(
                {
                    "q": question,
                    "rq": round(float(result.retrieval_quality), 4),
                    "retries": int(result.retries),
                    "chunks": len(result.citations or []),
                    "answer_head": (result.answer or "")[:140].replace("\n", " "),
                }
            )
        )

    print("WORST_EVAL")
    for row in sorted(eval_rows, key=lambda item: float(item["rq"]))[:8]:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
