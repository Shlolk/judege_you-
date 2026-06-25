import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from core.models.project import Project
from ai.models.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureAnalysis:
    score: float
    risk_level: str
    pattern: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    technical_debt: float
    scalability_rating: float
    maintainability_rating: float
    innovation_rating: float


class ArchitectureAuditor:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    async def analyze_architecture(self, project: Project, include_weak_points: bool = True) -> ArchitectureAnalysis:
        analysis = await self.ollama_client.generate_structured(
            f"Analyze architecture of project '{project.name}': {project.description}. "
            "Return JSON with: score (0-100), risk_level (low/medium/high/critical), pattern, "
            "strengths (list), weaknesses (list), recommendations (list), "
            "technical_debt (0-100), scalability_rating (0-100), "
            "maintainability_rating (0-100), innovation_rating (0-100)")

        if analysis and "score" in analysis:
            valid_keys = {f.name for f in __import__("dataclasses").fields(ArchitectureAnalysis)}
            filtered = {k: v for k, v in analysis.items() if k in valid_keys}
            return ArchitectureAnalysis(**filtered)
        return self._fallback()

    def _fallback(self) -> ArchitectureAnalysis:
        return ArchitectureAnalysis(score=72.0, risk_level="medium", pattern="Modular Monolith",
                                    strengths=["Clean separation of concerns", "Good documentation"],
                                    weaknesses=["Limited horizontal scalability", "No caching layer"],
                                    recommendations=["Add caching", "Consider event-driven architecture",
                                                     "Implement health checks"],
                                    technical_debt=25.0, scalability_rating=65.0,
                                    maintainability_rating=78.0, innovation_rating=60.0)

    async def identify_architectural_patterns(self, project: Project) -> List[str]:
        response = await self.ollama_client.generate(
            f"Identify architectural patterns in '{project.name}': {project.description}")
        return [l.strip() for l in response.splitlines() if l.strip() and not l.startswith("Score:")] or [
            "Layered Architecture", "Repository Pattern", "Dependency Injection"]

    async def calculate_architecture_risk_score(self, project: Project) -> float:
        return await self._mock_risk_score(project)

    async def _mock_risk_score(self, project: Project) -> float:
        import random
        return min(100, max(0, 30 + random.randint(-10, 10)))
