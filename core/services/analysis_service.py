import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..models.project import Project
from ..models.analysis import AnalysisResult

logger = logging.getLogger(__name__)

@dataclass
class ProjectAnalysisResult:
    project_id: str
    architecture_score: float = 0.0
    innovation_score: float = 0.0
    technical_debt_score: float = 0.0
    hackathon_readiness_score: float = 0.0
    team_readiness_score: float = 0.0
    competitive_advantage_score: float = 0.0
    overall_score: float = 0.0
    weak_points: List[str] = None
    strength_points: List[str] = None
    recommendations: List[str] = None
    risk_level: str = "medium"
    market_position: Dict[str, Any] = None
    technical_summary: Dict[str, Any] = None
    innovation_potential: Dict[str, Any] = None
    team_composition: Dict[str, Any] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.weak_points is None:
            self.weak_points = []
        if self.strength_points is None:
            self.strength_points = []
        if self.recommendations is None:
            self.recommendations = []
        if self.market_position is None:
            self.market_position = {}
        if self.technical_summary is None:
            self.technical_summary = {}
        if self.innovation_potential is None:
            self.innovation_potential = {}
        if self.team_composition is None:
            self.team_composition = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.overall_score == 0.0:
            self.overall_score = self._calculate_overall()

    def _calculate_overall(self) -> float:
        scores = [self.architecture_score, self.innovation_score,
                  (100 - self.technical_debt_score), self.hackathon_readiness_score,
                  self.team_readiness_score, self.competitive_advantage_score]
        return sum(scores) / len(scores) if scores else 0.0

    def recalculate(self):
        self.overall_score = self._calculate_overall()


class AnalysisService:
    def __init__(self, project_repository=None, analysis_repository=None,
                 ollama_client=None, embedding_service=None,
                 code_parser=None, document_parser=None, ppt_parser=None,
                 architecture_auditor=None, hackathon_engine=None,
                 weakness_engine=None, competitor_engine=None):
        self.project_repository = project_repository
        self.analysis_repository = analysis_repository
        self.ollama_client = ollama_client
        self.embedding_service = embedding_service
        self.code_parser = code_parser
        self.document_parser = document_parser
        self.ppt_parser = ppt_parser
        self._modules = {
            "architecture": architecture_auditor,
            "hackathon": hackathon_engine,
            "weakness": weakness_engine,
            "competitive": competitor_engine,
        }

    async def analyze_project(self, project_id: str,
                              analysis_types: Optional[List[str]] = None) -> ProjectAnalysisResult:
        if analysis_types is None:
            analysis_types = ["architecture", "hackathon", "innovation",
                              "technical-debt", "team-readiness", "competitive-advantage"]

        project = None
        if self.project_repository:
            project = await self.project_repository.get_by_id(project_id)

        if project is None:
            project = Project.create(name=f"Project-{project_id[:8]}", description="Auto-created for analysis")
            project.id = project_id

        result = ProjectAnalysisResult(project_id=project_id)
        logger.info(f"Starting analysis for project {project_id}: {analysis_types}")

        # Run architecture analysis
        if "architecture" in analysis_types:
            try:
                arch_mod = self._modules.get("architecture")
                if not arch_mod:
                    raise RuntimeError("Architecture auditor not available")
                arch = await arch_mod.analyze_architecture(project)
                result.architecture_score = arch.score
            except Exception as e:
                logger.warning(f"Architecture analysis failed: {e}")
                result.architecture_score = 65.0

        # Run hackathon readiness
        if "hackathon" in analysis_types:
            try:
                hack_mod = self._modules.get("hackathon")
                if not hack_mod:
                    raise RuntimeError("Hackathon engine not available")
                readiness = await hack_mod.evaluate_hackathon_readiness(project)
                result.hackathon_readiness_score = readiness.overall_score
                result.team_readiness_score = readiness.evaluation_criteria.get("team_coordination_score", 65.0)
            except Exception as e:
                logger.warning(f"Hackathon analysis failed: {e}")
                result.hackathon_readiness_score = 65.0

        # Run innovation analysis (use AI)
        if "innovation" in analysis_types:
            try:
                result.innovation_score = await self._analyze_innovation(project)
            except Exception as e:
                logger.warning(f"Innovation analysis failed: {e}")
                result.innovation_score = 65.0

        # Run technical debt analysis (use weakness detection)
        if "technical-debt" in analysis_types:
            try:
                weak_mod = self._modules.get("weakness")
                if not weak_mod:
                    raise RuntimeError("Weakness detection not available")
                weakness = await weak_mod.detect_weaknesses(project)
                result.technical_debt_score = weakness.overall_weakness_score
            except Exception as e:
                logger.warning(f"Weakness detection failed: {e}")
                result.technical_debt_score = 25.0

        # Run team readiness
        if "team-readiness" in analysis_types and result.team_readiness_score == 0.0:
            result.team_readiness_score = 70.0

        # Run competitive analysis
        if "competitive-advantage" in analysis_types:
            try:
                comp_mod = self._modules.get("competitive")
                if not comp_mod:
                    raise RuntimeError("Competitive analysis not available")
                comp = await comp_mod.analyze_competition(project)
                result.competitive_advantage_score = comp.competitiveness_score
            except Exception as e:
                logger.warning(f"Competitive analysis failed: {e}")
                result.competitive_advantage_score = 65.0

        # Recalculate overall score and derive weak/strong points
        result.recalculate()
        result.risk_level = self._risk_level(result.overall_score)
        result.weak_points = self._weak_points(result)
        result.strength_points = self._strength_points(result)
        result.recommendations = self._recommendations(result)

        if self.analysis_repository:
            await self.analysis_repository.save(project_id, AnalysisResult.from_project_analysis(
                project_id, "comprehensive", result))

        return result

    async def _analyze_innovation(self, project: Project) -> float:
        """Analyze innovation using AI"""
        if self.ollama_client:
            try:
                resp = await self.ollama_client.generate(
                    f"Analyze the innovation potential of this project:\n"
                    f"Name: {project.name}\n"
                    f"Description: {project.description}\n"
                    f"Return only a number 0-100 representing innovation score."
                )
                import re
                match = re.search(r'(\d+\.?\d*)', resp)
                if match:
                    return min(100, max(0, float(match.group(1))))
            except Exception:
                pass
        return 72.0

    def _risk_level(self, score: float) -> str:
        if score >= 80:
            return "low"
        elif score >= 65:
            return "medium"
        elif score >= 50:
            return "high"
        return "critical"

    def _weak_points(self, r: ProjectAnalysisResult) -> List[str]:
        w = []
        if r.architecture_score < 70:
            w.append("Architecture complexity needs attention")
        if r.technical_debt_score > 30:
            w.append("Technical debt requires refactoring")
        if r.team_readiness_score < 65:
            w.append("Team skill gaps identified")
        if r.innovation_score < 60:
            w.append("Limited innovation differentiation")
        if r.competitive_advantage_score < 60:
            w.append("Weak competitive positioning")
        if r.hackathon_readiness_score < 65:
            w.append("Low hackathon readiness")
        return w

    def _strength_points(self, r: ProjectAnalysisResult) -> List[str]:
        s = []
        if r.architecture_score >= 85:
            s.append("Robust and scalable architecture")
        if r.innovation_score >= 85:
            s.append("Strong innovation potential")
        if r.team_readiness_score >= 85:
            s.append("High team readiness")
        if r.competitive_advantage_score >= 85:
            s.append("Strong competitive advantage")
        if r.hackathon_readiness_score >= 80:
            s.append("Excellent hackathon readiness")
        return s if s else ["Solid project foundation"]

    def _recommendations(self, r: ProjectAnalysisResult) -> List[str]:
        recs = []
        if r.architecture_score < 70:
            recs.append("Refactor architecture for better maintainability")
        if r.technical_debt_score > 30:
            recs.append("Address technical debt systematically")
        if r.team_readiness_score < 65:
            recs.append("Invest in team skill development")
        if r.innovation_score < 60:
            recs.append("Increase innovation differentiation")
        if r.competitive_advantage_score < 60:
            recs.append("Strengthen competitive positioning")
        if r.risk_level in ("high", "critical"):
            recs.append("Implement risk mitigation strategies immediately")
        return recs if recs else ["Continue current trajectory - strong potential"]
