"""Analysis API routes"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.architecture_auditor import ArchitectureAuditor
from modules.hackathon_readiness_engine import HackathonReadinessEngine
from modules.weakness_detection_engine import WeaknessDetectionEngine
from modules.judge_simulation_engine import JudgeSimulationEngine
from modules.ai_reasoning_engine import AIReasoningEngine
from models.project import Project

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
    """Run analysis on a project"""
    
    project = Project.create(
        name=request.project_name,
        description=request.project_description,
    )
    project.id = request.project_id
    
    results = {}
    
    # Run requested analyses
    if "architecture" in request.analysis_types:
        auditor = ArchitectureAuditor(ollama_client=None)
        arch_result = await auditor.analyze_architecture(project)
        results["architecture_score"] = arch_result.score
        results["architecture_risk"] = arch_result.risk_level
    
    if "hackathon" in request.analysis_types:
        engine = HackathonReadinessEngine(ollama_client=None)
        readiness = await engine.evaluate_hackathon_readiness(project)
        results["hackathon_readiness"] = readiness.overall_score
    
    if "weakness" in request.analysis_types:
        detector = WeaknessDetectionEngine(
            ollama_client=None,
            code_parser=None,
            document_parser=None,
        )
        weakness_report = await detector.detect_weaknesses(project)
        results["weakness_count"] = len(weakness_report.weaknesses)
        results["weakness_score"] = weakness_report.overall_weakness_score
    
    # Calculate overall score
    scores = {
        "architecture": results.get("architecture_score", 0),
        "hackathon_readiness": results.get("hackathon_readiness", 0),
        "technical_debt": 100 - results.get("weakness_score", 50),
        "innovation": 75.0,
        "team_readiness": 70.0,
        "competitive_advantage": 65.0,
    }
    
    overall_score = sum(scores.values()) / len(scores)
    
    return AnalysisResponse(
        project_id=request.project_id,
        overall_score=overall_score,
        scores=scores,
        strengths=[
            "Strong architectural foundation",
            "Good innovation potential",
            "Active development",
        ],
        weak_spots=[
            "Limited test coverage",
            "Technical debt accumulation",
            "Documentation gaps",
        ],
        recommendations=[
            "Increase test coverage to >60%",
            "Address high-priority technical debt",
            "Create comprehensive documentation",
            "Prepare for judge simulation",
        ],
    )

@router.get("/{project_id}/scores")
async def get_analysis_scores(project_id: str):
    """Get analysis scores for a project"""
    return {
        "project_id": project_id,
        "scores": {
            "architecture": 85.0,
            "innovation": 78.0,
            "hackathon_readiness": 72.0,
            "technical_debt": 25.0,
            "team_readiness": 80.0,
            "competitive_advantage": 70.0,
        },
        "overall": 75.0,
    }
