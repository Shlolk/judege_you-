import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random

from core.models.project import Project
from ai.models.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class HackathonReadinessResult:
    overall_score: float
    presentation_ready: bool
    demo_ready: bool
    team_ready: bool
    mentor_required: bool
    timeline_feasible: bool
    competition_level: str
    winning_probability: float
    key_weaknesses: List[str]
    key_strengths: List[str]
    improvement_recommendations: List[str]
    evaluation_criteria: Dict[str, float]


@dataclass
class TeamComposition:
    total_members: int = 0
    senior_members: int = 0
    mid_level_members: int = 0
    junior_members: int = 0
    skill_diversity_score: float = 0.0
    role_coverage_score: float = 0.0
    availability_score: float = 0.0
    expertise_score: float = 0.0
    communication_score: float = 0.0
    overall_team_score: float = 0.0


class HackathonReadinessEngine:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    async def evaluate_hackathon_readiness(
            self, project: Project, team_composition: Optional[TeamComposition] = None,
            include_detailed_analysis: bool = True) -> HackathonReadinessResult:

        project_scores = await self._eval_project(project)
        team_scores = self._eval_team(team_composition) if team_composition else self._default_team()

        overall = project_scores["overall_score"] * 0.6 + team_scores["overall_score"] * 0.4

        weaknesses = await self._weaknesses(project, overall)
        strengths = await self._strengths(project, overall)

        return HackathonReadinessResult(
            overall_score=overall,
            presentation_ready=overall >= 70,
            demo_ready=project_scores["demo_score"] >= 70,
            team_ready=team_scores["overall_score"] >= 65,
            mentor_required=overall < 60,
            timeline_feasible=overall >= 55,
            competition_level="medium" if overall < 75 else "high",
            winning_probability=min(90, max(10, overall * 0.8)),
            key_weaknesses=weaknesses,
            key_strengths=strengths,
            improvement_recommendations=self._recommendations(weaknesses, team_scores),
            evaluation_criteria={
                "technical_score": project_scores.get("technical_score", 65),
                "presentation_score": project_scores.get("presentation_score", 60),
                "team_coordination_score": team_scores.get("coordination_score", 60),
                "innovation_score": project_scores.get("innovation_score", 70),
                "market_fit_score": project_scores.get("market_score", 55),
            }
        )

    async def _eval_project(self, project: Project) -> Dict[str, float]:
        response = await self.ollama_client.generate_structured(
            f"Evaluate '{project.name}' hackathon readiness: {project.description}. "
            "Return JSON with scores (0-100): overall_score, technical_score, "
            "presentation_score, innovation_score, market_score, demo_score, "
            "timeline_feasibility_score, resource_requirement_score")
        return response if response and "overall_score" in response else {
            "overall_score": 65.0, "technical_score": 68.0, "presentation_score": 60.0,
            "innovation_score": 72.0, "market_score": 55.0, "demo_score": 62.0,
            "timeline_feasibility_score": 70.0, "resource_requirement_score": 58.0}

    def _eval_team(self, team: TeamComposition) -> Dict[str, float]:
        return {"overall_score": team.overall_team_score,
                "coordination_score": team.communication_score,
                "technical_readiness_score": team.expertise_score,
                "presentation_skills_score": team.skill_diversity_score * 50 + 30,
                "time_management_score": team.availability_score,
                "innovation_capacity_score": min(100, team.skill_diversity_score * 60 + 20),
                "mentor_needed": team.overall_team_score < 65,
                "critical_gaps": ["Skill depth", "Presentation practice"] if team.overall_team_score < 70 else []}

    def _default_team(self) -> Dict[str, float]:
        return {"overall_score": 60.0, "coordination_score": 65.0,
                "technical_readiness_score": 62.0, "presentation_skills_score": 55.0,
                "time_management_score": 70.0, "innovation_capacity_score": 58.0,
                "mentor_needed": True,
                "critical_gaps": ["Team composition", "Skill balance"]}

    async def _weaknesses(self, project: Project, overall: float) -> List[str]:
        return ["Technical debt accumulation", "Limited team experience",
                "Incomplete documentation", "Scope creep risk"]

    async def _strengths(self, project: Project, overall: float) -> List[str]:
        return ["Innovative solution approach", "Strong team commitment",
                "Clear value proposition", "Technical feasibility"]

    def _recommendations(self, weaknesses: List[str], team: Dict) -> List[str]:
        recs = []
        for w in weaknesses:
            if "technical" in w.lower():
                recs.append("Refactor code and improve architecture")
            elif "team" in w.lower():
                recs.append("Add experienced members or mentors")
            elif "documentation" in w.lower():
                recs.append("Create comprehensive documentation")
            elif "scope" in w.lower():
                recs.append("Define clear milestones")
        if team.get("mentor_needed"):
            recs.append("Secure technical mentor")
        return recs[:6] or ["Focus on MVP", "Improve communication"]
