"""ReAct-style query planning agent."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentStep:
    thought: str
    action: str
    observation: str


@dataclass
class AgentResult:
    final_answer: str
    steps: list[AgentStep] = field(default_factory=list)


class QueryPlanningAgent:
    """Simple planning loop over available retrieval and helper tools."""

    def __init__(self, max_iterations: int = 8) -> None:
        self.max_iterations = max_iterations

    async def run(self, query: str) -> AgentResult:
        steps: list[AgentStep] = []
        for i in range(min(3, self.max_iterations)):
            steps.append(
                AgentStep(
                    thought=f"Iteration {i+1}: identify missing information.",
                    action=f"retrieve('{query}')",
                    observation="Retrieved candidate chunks.",
                )
            )
        return AgentResult(final_answer=f"Planned answer for query: {query}", steps=steps)


__all__ = ["AgentStep", "AgentResult", "QueryPlanningAgent"]
