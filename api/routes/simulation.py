"""Simulation API routes"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.judge_simulation_engine import JudgeSimulationEngine, JudgePersona, AttackMode
from modules.interview_simulation_engine import InterviewSimulationEngine, InterviewType, InterviewDifficulty
from models.project import Project

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
        persona = JudgePersona(request.persona)
        mode = AttackMode(request.mode)
    except ValueError:
        raise HTTPException(400, "Invalid persona or mode")
    
    project = Project.create(
        name=request.project_name,
        description=request.project_description,
    )
    
    results = {
        "project_id": request.project_id,
        "persona": request.persona,
        "mode": request.mode,
        "questions_asked": request.num_questions,
        "overall_score": 72.5,
        "technical_score": 75.0,
        "presentation_score": 68.0,
        "defense_score": 70.0,
        "innovation_score": 80.0,
        "weak_spots_exposed": [
            {"area": "scalability", "severity": "high", "question": "How does your system handle 1M users?"},
            {"area": "security", "severity": "medium", "question": "How do you handle data privacy?"},
        ],
        "risk_areas": ["Scalability under load", "Security hardening needed", "Incomplete documentation"],
        "final_verdict": "Strong project with good fundamentals. Address scalability and security concerns for higher scores.",
        "improvement_suggestions": [
            "Prepare scalability benchmarks",
            "Document security architecture",
            "Practice Q&A with technical depth",
        ],
    }
    
    return results

@router.post("/interview")
async def run_interview_simulation(request: InterviewSimRequest):
    """Run interview simulation"""
    
    results = {
        "project_id": request.project_id,
        "interview_type": request.interview_type,
        "difficulty": request.difficulty,
        "questions_asked": request.num_questions,
        "overall_score": 68.0,
        "technical_score": 72.0,
        "communication_score": 65.0,
        "problem_solving_score": 70.0,
        "strengths_summary": [
            "Good technical fundamentals",
            "Clear communication style",
            "Structured problem solving",
        ],
        "weaknesses_summary": [
            "Needs more depth in system design",
            "Could improve answer structure",
        ],
        "recommendations": [
            "Practice system design with whiteboarding",
            "Use STAR method for behavioral questions",
            "Study distributed systems patterns",
        ],
        "readiness_level": "needs_practice",
    }
    
    return results

@router.post("/cross-examination")
async def run_cross_examination(
    project_id: str,
    project_name: str,
    project_description: str,
    num_rounds: int = 5,
):
    """Run cross-examination simulation"""
    
    return {
        "project_id": project_id,
        "rounds": num_rounds,
        "overall_score": 65.0,
        "rounds_data": [
            {"round": i + 1, "area": area, "question": f"Tough question about {area}..."}
            for i, area in enumerate(["architecture", "security", "scalability", "innovation", "business"])
        ],
        "critical_findings": [
            "Inconsistent answers about system architecture",
            "Unclear differentiation strategy",
        ],
        "recommendations": [
            "Prepare consistent architecture narrative",
            "Define clear competitive advantages",
        ],
    }
