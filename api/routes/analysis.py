"""Analysis API routes"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalysisRequest(BaseModel):
    project_id: str
    project_name: str
    project_description: str
    analysis_types: List[str] = ["architecture", "hackathon", "weakness"]

class AnalysisResponse(BaseModel):
    project_id: str
    overall_score: float
    scores: dict
    strengths: list
    weak_spots: list
    recommendations: list

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_project(request: AnalysisRequest):
    """Run analysis on a project using the analysis service"""
    try:
        from core.di.container import container
        from core.models.project import Project

        analyzer = container.get("analysis_service")
        if not analyzer:
            raise HTTPException(status_code=503, detail="Analysis service not available")

        # Map CLI-style analysis types to what the service expects
        type_map = {
            "architecture": "architecture",
            "hackathon": "hackathon",
            "innovation": "innovation",
            "technical-debt": "technical-debt",
            "weakness": "technical-debt",
            "team": "team-readiness",
            "competitive": "competitive-advantage",
        }
        service_types = [type_map.get(t, t) for t in request.analysis_types if t in type_map]

        project = Project.create(name=request.project_name, description=request.project_description)
        project.id = request.project_id

        result = await analyzer.analyze_project(project.id, service_types)

        return AnalysisResponse(
            project_id=request.project_id,
            overall_score=result.overall_score,
            scores={
                "architecture": result.architecture_score,
                "innovation": result.innovation_score,
                "hackathon_readiness": result.hackathon_readiness_score,
                "technical_debt": result.technical_debt_score,
                "team_readiness": result.team_readiness_score,
                "competitive_advantage": result.competitive_advantage_score,
            },
            strengths=result.strength_points or ["Solid project foundation"],
            weak_spots=result.weak_points or [],
            recommendations=result.recommendations or [],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/architecture")
async def analyze_architecture(project_id: str, project_name: str, project_description: str):
    """Run architecture-specific analysis"""
    try:
        from core.di.container import container
        from core.models.project import Project

        auditor = container.get("architecture_auditor")
        if not auditor:
            raise HTTPException(status_code=503, detail="Architecture auditor not available")

        project = Project.create(name=project_name, description=project_description)
        result = await auditor.analyze_architecture(project)

        return {
            "project_id": project_id,
            "architecture_score": result.score,
            "risk_level": result.risk_level,
            "pattern": result.pattern,
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "recommendations": result.recommendations,
            "technical_debt": result.technical_debt,
            "scalability": result.scalability_rating,
            "maintainability": result.maintainability_rating,
        }
    except Exception as e:
        logger.exception("Architecture analysis failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hackathon-readiness")
async def hackathon_readiness(project_id: str, project_name: str, project_description: str):
    """Run hackathon readiness analysis"""
    try:
        from core.di.container import container
        from core.models.project import Project

        engine = container.get("hackathon_readiness")
        if not engine:
            raise HTTPException(status_code=503, detail="Hackathon readiness engine not available")

        project = Project.create(name=project_name, description=project_description)
        result = await engine.evaluate_hackathon_readiness(project)

        return {
            "project_id": project_id,
            "overall_score": result.overall_score,
            "winning_probability": result.winning_probability,
            "competition_level": result.competition_level,
            "presentation_ready": result.presentation_ready,
            "demo_ready": result.demo_ready,
            "team_ready": result.team_ready,
            "mentor_required": result.mentor_required,
            "key_strengths": result.key_strengths,
            "key_weaknesses": result.key_weaknesses,
            "recommendations": result.improvement_recommendations,
            "evaluation_criteria": result.evaluation_criteria,
        }
    except Exception as e:
        logger.exception("Hackathon readiness analysis failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/scores")
async def get_analysis_scores(project_id: str):
    """Get analysis scores for a project"""
    try:
        from core.di.container import container

        analyzer = container.get("analysis_service")
        if not analyzer:
            raise HTTPException(status_code=503, detail="Analysis service not available")

        result = await analyzer.analyze_project(project_id)

        return {
            "project_id": project_id,
            "scores": {
                "architecture": result.architecture_score,
                "innovation": result.innovation_score,
                "hackathon_readiness": result.hackathon_readiness_score,
                "technical_debt": result.technical_debt_score,
                "team_readiness": result.team_readiness_score,
                "competitive_advantage": result.competitive_advantage_score,
            },
            "overall": result.overall_score,
            "risk_level": result.risk_level,
        }
    except Exception as e:
        logger.exception("Failed to get scores")
        raise HTTPException(status_code=500, detail=str(e))
