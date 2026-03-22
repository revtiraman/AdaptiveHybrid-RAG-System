"""RAGAS-style evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RAGASMetrics:
	faithfulness: float
	answer_relevancy: float
	context_precision: float
	context_recall: float
	answer_correctness: float


@dataclass
class EvalSample:
	question: str
	answer: str
	contexts: list[str]
	ground_truth: str | None = None


@dataclass
class EvalReport:
	size: int
	average: RAGASMetrics
	by_sample: list[RAGASMetrics]


class RAGASEvaluator:
	"""Compute lightweight stand-ins for RAGAS metrics."""

	async def evaluate_single(
		self,
		question: str,
		answer: str,
		contexts: list[str],
		ground_truth: str | None,
	) -> RAGASMetrics:
		q_terms = set(_tokens(question))
		a_terms = set(_tokens(answer))
		c_terms = set(_tokens(" ".join(contexts)))
		g_terms = set(_tokens(ground_truth or ""))

		faithfulness = _safe_ratio(len(a_terms & c_terms), len(a_terms))
		answer_relevancy = _safe_ratio(len(q_terms & a_terms), len(q_terms))
		context_precision = _safe_ratio(len(c_terms & q_terms), len(c_terms))
		context_recall = _safe_ratio(len(c_terms & q_terms), len(q_terms))
		answer_correctness = (
			_safe_ratio(len(a_terms & g_terms), len(g_terms)) if ground_truth else 0.5 * answer_relevancy + 0.5 * faithfulness
		)

		return RAGASMetrics(
			faithfulness=float(_clip01(faithfulness)),
			answer_relevancy=float(_clip01(answer_relevancy)),
			context_precision=float(_clip01(context_precision)),
			context_recall=float(_clip01(context_recall)),
			answer_correctness=float(_clip01(answer_correctness)),
		)

	async def evaluate_dataset(self, dataset: list[EvalSample], batch_size: int = 10) -> EvalReport:
		metrics: list[RAGASMetrics] = []
		for sample in dataset:
			metrics.append(
				await self.evaluate_single(
					question=sample.question,
					answer=sample.answer,
					contexts=sample.contexts,
					ground_truth=sample.ground_truth,
				)
			)

		if not metrics:
			zero = RAGASMetrics(0.0, 0.0, 0.0, 0.0, 0.0)
			return EvalReport(size=0, average=zero, by_sample=[])

		avg = RAGASMetrics(
			faithfulness=sum(m.faithfulness for m in metrics) / len(metrics),
			answer_relevancy=sum(m.answer_relevancy for m in metrics) / len(metrics),
			context_precision=sum(m.context_precision for m in metrics) / len(metrics),
			context_recall=sum(m.context_recall for m in metrics) / len(metrics),
			answer_correctness=sum(m.answer_correctness for m in metrics) / len(metrics),
		)
		return EvalReport(size=len(metrics), average=avg, by_sample=metrics)


def _tokens(text: str) -> list[str]:
	return [w.lower() for w in __import__("re").findall(r"[A-Za-z0-9_\-]+", text or "") if len(w) > 2]


def _safe_ratio(num: int, denom: int) -> float:
	return num / denom if denom else 0.0


def _clip01(val: float) -> float:
	return max(0.0, min(1.0, val))


__all__ = ["RAGASMetrics", "EvalSample", "EvalReport", "RAGASEvaluator"]
