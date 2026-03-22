from __future__ import annotations

from dataclasses import dataclass

from research_rag.hybrid.config import HybridRAGSettings
from research_rag.hybrid.orchestrator import HybridRAGSystem
from research_rag.logging import configure_logging


@dataclass(slots=True)
class ServiceContainer:
    settings: HybridRAGSettings
    system: HybridRAGSystem


def build_container(settings: HybridRAGSettings | None = None) -> ServiceContainer:
    resolved_settings = settings or HybridRAGSettings.from_env()
    configure_logging("INFO")

    system = HybridRAGSystem(resolved_settings)

    return ServiceContainer(
        settings=resolved_settings,
        system=system,
    )
