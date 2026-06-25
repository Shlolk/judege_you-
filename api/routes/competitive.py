"""Competitive intelligence API routes"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CompetitiveAnalysisRequest(BaseModel):
    project_name: str
    project_description: str
    market_segments: Optional[list] = None

@router.post("/analyze")
async def analyze_competition(request: CompetitiveAnalysisRequest):
    """Analyze competitive landscape"""
    try:
        from core.di.container import container
        from core.models.project import Project

        competitor = container.get("competitor_analysis")
        if not competitor:
            raise HTTPException(status_code=503, detail="Competitor analysis engine not available")

        project = Project.create(name=request.project_name, description=request.project_description)
        result = await competitor.analyze_competition(project)

        return {
            "project_name": request.project_name,
            "overall_position": result.overall_position,
            "competitiveness_score": result.competitiveness_score,
            "market_fit_score": result.market_fit_score,
            "differentiation_score": result.differentiation_score,
            "direct_competitors": [
                {
                    "name": c.name,
                    "strengths": c.strengths[:3],
                    "weaknesses": c.weaknesses[:3],
                    "threat_level": c.threat_level,
                    "similarity": c.similarity_score,
                }
                for c in result.direct_competitors[:5]
            ],
            "blue_ocean_opportunities": result.blue_ocean_opportunities[:5],
            "competitive_advantages": result.competitive_advantages[:5],
            "competitive_disadvantages": result.competitive_disadvantages[:3],
            "strategic_recommendations": result.strategic_recommendations[:8],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Competitive analysis failed")
        raise HTTPException(status_code=500, detail=str(e))
