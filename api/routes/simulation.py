"""Simulation API routes"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class JudgeSimRequest(BaseModel):
    project_id: str
    project_name: str
    project_description: str
    persona: str = "sih_judge"
    mode: str = "moderate"
    num_questions: int = 10

class InterviewSimRequest(BaseModel):
    project_id: str
    project_name: str
    project_description: str
    interview_type: str = "technical"
    difficulty: str = "mid"
    num_questions: int = 8

@router.post("/judge")
async def run_judge_simulation(request: JudgeSimRequest):
    """Run judge simulation"""
    try:
        from core.di.container import container
        from core.models.project import Project
        from modules.judge_simulation_engine import JudgePersona, AttackMode

        judge = container.get("judge_simulation")
        if not judge:
            raise HTTPException(status_code=503, detail="Judge simulation engine not available")

        try:
            persona = JudgePersona(request.persona)
            mode = AttackMode(request.mode)
        except ValueError:
            raise HTTPException(400, f"Invalid persona '{request.persona}' or mode '{request.mode}'")

        project = Project.create(name=request.project_name, description=request.project_description)
        project.id = request.project_id

        result = await judge.run_simulation(project, persona=persona, mode=mode, num_questions=request.num_questions)

        return {
            "project_id": request.project_id,
            "persona": request.persona,
            "mode": request.mode,
            "overall_score": result.overall_score,
            "technical_score": result.technical_score,
            "presentation_score": result.presentation_score,
            "defense_score": result.defense_score,
            "innovation_score": result.innovation_score,
            "weak_spots_exposed": result.weak_spots_exposed,
            "risk_areas": result.risk_areas,
            "final_verdict": result.final_verdict,
            "improvement_suggestions": result.improvement_suggestions,
            "questions_asked": [
                {"question": q.question, "category": q.category, "difficulty": q.difficulty}
                for q in result.questions_asked[:5]
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Judge simulation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview")
async def run_interview_simulation(request: InterviewSimRequest):
    """Run interview simulation"""
    try:
        from core.di.container import container
        from core.models.project import Project
        from modules.interview_simulation_engine import InterviewType, InterviewDifficulty

        interview = container.get("interview_simulation")
        if not interview:
            raise HTTPException(status_code=503, detail="Interview simulation engine not available")

        try:
            itype = InterviewType(request.interview_type)
            diff = InterviewDifficulty(request.difficulty)
        except ValueError:
            raise HTTPException(400, f"Invalid interview type '{request.interview_type}' or difficulty '{request.difficulty}'")

        project = Project.create(name=request.project_name, description=request.project_description)

        result = await interview.run_interview(
            project, interview_type=itype, difficulty=diff, num_questions=request.num_questions, simulate_candidate=True
        )

        return {
            "project_id": request.project_id,
            "interview_type": request.interview_type,
            "difficulty": request.difficulty,
            "overall_score": result.overall_score,
            "technical_score": result.technical_score,
            "communication_score": result.communication_score,
            "problem_solving_score": result.problem_solving_score,
            "strengths_summary": result.strengths_summary,
            "weaknesses_summary": result.weaknesses_summary,
            "recommendations": result.recommendations,
            "readiness_level": result.readiness_level,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Interview simulation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cross-examination")
async def run_cross_examination(
    project_id: str, project_name: str, project_description: str, num_rounds: int = 5
):
    """Run cross-examination simulation"""
    try:
        from core.di.container import container
        from core.models.project import Project

        judge = container.get("judge_simulation")
        if not judge:
            raise HTTPException(status_code=503, detail="Judge simulation engine not available")

        project = Project.create(name=project_name, description=project_description)

        result = await judge.cross_examination(project, num_rounds=num_rounds)

        return {
            "project_id": project_id,
            "rounds": num_rounds,
            "overall_score": result["overall_score"],
            "rounds_data": result["rounds"],
            "critical_findings": result["critical_findings"],
            "recommendations": result["recommendations"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Cross-examination failed")
        raise HTTPException(status_code=500, detail=str(e))
