"""Benchmark runner for retrieval and answer quality experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .latency_profiler import LatencyProfiler
from .ragas_evaluator import EvalSample, RAGASEvaluator


@dataclass
class BenchmarkReport:
	timestamp: str
	config_results: dict[str, dict[str, Any]]
	latency_summary: dict[str, dict[str, float]]
	output_json: str
	output_html: str


class BenchmarkRunner:
	"""Run ablation-style benchmarks over evaluation datasets."""

	def __init__(self, eval_dir: str | Path = "data/eval_datasets") -> None:
		self.eval_dir = Path(eval_dir)
		self.evaluator = RAGASEvaluator()
		self.profiler = LatencyProfiler()

	async def run_full_benchmark(self) -> BenchmarkReport:
		dataset = self._load_dataset()
		configs = ["vector_only", "bm25_only", "hybrid", "hybrid+rerank", "hybrid+rerank+adaptive", "full_system"]

		config_results: dict[str, dict[str, Any]] = {}
		for config in configs:
			with self.profiler.track(config):
				metrics = await self.evaluator.evaluate_dataset(dataset)
			config_results[config] = {
				"faithfulness": metrics.average.faithfulness,
				"answer_relevancy": metrics.average.answer_relevancy,
				"context_precision": metrics.average.context_precision,
				"context_recall": metrics.average.context_recall,
				"answer_correctness": metrics.average.answer_correctness,
				"samples": metrics.size,
			}

		timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
		out_dir = Path("eval_results")
		out_dir.mkdir(parents=True, exist_ok=True)
		json_path = out_dir / f"{timestamp}.json"
		html_path = out_dir / f"{timestamp}.html"

		payload = {
			"timestamp": timestamp,
			"config_results": config_results,
			"latency_summary": self.profiler.summary(),
		}
		json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
		html_path.write_text(self._render_html(payload), encoding="utf-8")

		return BenchmarkReport(
			timestamp=timestamp,
			config_results=config_results,
			latency_summary=self.profiler.summary(),
			output_json=str(json_path),
			output_html=str(html_path),
		)

	def _load_dataset(self) -> list[EvalSample]:
		custom = self.eval_dir / "custom_qa.jsonl"
		if custom.exists():
			items: list[EvalSample] = []
			for line in custom.read_text(encoding="utf-8").splitlines():
				if not line.strip():
					continue
				obj = json.loads(line)
				items.append(
					EvalSample(
						question=obj.get("question", ""),
						answer=obj.get("answer", ""),
						contexts=obj.get("contexts", []),
						ground_truth=obj.get("ground_truth"),
					)
				)
			if items:
				return items

		return [
			EvalSample(
				question="What is retrieval augmented generation?",
				answer="Retrieval augmented generation combines retrieval with language model generation.",
				contexts=["RAG uses external context retrieval before generation."],
				ground_truth="RAG combines retrieval and generation.",
			),
			EvalSample(
				question="Why use hybrid retrieval?",
				answer="Hybrid retrieval balances lexical and semantic matching.",
				contexts=["Hybrid retrieval combines dense vectors and BM25."],
				ground_truth="Hybrid retrieval improves recall by combining sparse and dense methods.",
			),
		]

	def _render_html(self, payload: dict[str, Any]) -> str:
		rows = []
		for name, values in payload["config_results"].items():
			rows.append(
				f"<tr><td>{name}</td><td>{values['faithfulness']:.3f}</td><td>{values['answer_relevancy']:.3f}</td>"
				f"<td>{values['context_precision']:.3f}</td><td>{values['context_recall']:.3f}</td>"
				f"<td>{values['answer_correctness']:.3f}</td></tr>"
			)
		return (
			"<html><body><h1>Benchmark Report</h1><table border='1' cellpadding='6'>"
			"<tr><th>Config</th><th>Faithfulness</th><th>Relevancy</th><th>Ctx Precision</th><th>Ctx Recall</th><th>Correctness</th></tr>"
			+ "".join(rows)
			+ "</table></body></html>"
		)


__all__ = ["BenchmarkRunner", "BenchmarkReport"]
