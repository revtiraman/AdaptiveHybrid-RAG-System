"""Latency profiling helpers for end-to-end benchmark runs."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class LatencyProfiler:
	records: dict[str, list[float]] = field(default_factory=dict)

	@contextmanager
	def track(self, name: str):
		start = time.perf_counter()
		try:
			yield
		finally:
			elapsed = (time.perf_counter() - start) * 1000
			self.records.setdefault(name, []).append(elapsed)

	def summary(self) -> dict[str, dict[str, float]]:
		out: dict[str, dict[str, float]] = {}
		for key, vals in self.records.items():
			if not vals:
				continue
			out[key] = {
				"avg_ms": sum(vals) / len(vals),
				"min_ms": min(vals),
				"max_ms": max(vals),
				"count": float(len(vals)),
			}
		return out


__all__ = ["LatencyProfiler"]
