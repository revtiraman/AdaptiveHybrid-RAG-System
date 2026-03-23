from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvalCase:
    question: str
    expected_keywords: list[str]
    paper_ids: list[str] | None


class EvaluationHarness:
    def __init__(self, system) -> None:
        self.system = system

    def run(self, dataset_path: str | Path, limit: int | None = None) -> dict[str, Any]:
        cases = self._load_cases(dataset_path)
        if limit is not None and limit > 0:
            cases = cases[:limit]

        details: list[dict[str, Any]] = []
        total_keyword_recall = 0.0
        supported_count = 0
        total_quality = 0.0

        for case in cases:
            result = self.system.query(question=case.question, paper_ids=case.paper_ids)
            answer_lower = result.answer.lower()

            present = [kw for kw in case.expected_keywords if kw.lower() in answer_lower]
            recall = len(present) / max(1, len(case.expected_keywords)) if case.expected_keywords else 1.0
            verification = dict(result.diagnostic.get("verification", {}))
            is_supported = bool(verification.get("supported", False))

            total_keyword_recall += recall
            total_quality += float(result.retrieval_quality)
            if is_supported:
                supported_count += 1

            details.append(
                {
                    "question": case.question,
                    "expected_keywords": case.expected_keywords,
                    "matched_keywords": present,
                    "keyword_recall": round(recall, 4),
                    "retrieval_quality": round(float(result.retrieval_quality), 4),
                    "verification_supported": is_supported,
                    "retries": result.retries,
                    "latency_ms": result.latency_ms,
                }
            )

        n = max(1, len(cases))
        summary = {
            "cases": len(cases),
            "avg_keyword_recall": round(total_keyword_recall / n, 4),
            "supported_rate": round(supported_count / n, 4),
            "avg_retrieval_quality": round(total_quality / n, 4),
            "details": details,
        }
        return summary

    @staticmethod
    def _load_cases(dataset_path: str | Path) -> list[EvalCase]:
        path = Path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found: {path}")

        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return []

        payload: Any
        if text.startswith("["):
            payload = json.loads(text)
        else:
            payload = [json.loads(line) for line in text.splitlines() if line.strip()]

        cases: list[EvalCase] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            if not question:
                continue
            raw_keywords = item.get("expected_keywords", [])
            if isinstance(raw_keywords, list):
                expected_keywords = [str(x).strip() for x in raw_keywords if str(x).strip()]
            else:
                expected_keywords = []

            raw_paper_ids = item.get("paper_ids")
            paper_ids = None
            if isinstance(raw_paper_ids, list):
                paper_ids = [str(x).strip() for x in raw_paper_ids if str(x).strip()]

            cases.append(
                EvalCase(
                    question=question,
                    expected_keywords=expected_keywords,
                    paper_ids=paper_ids,
                )
            )

        return cases
