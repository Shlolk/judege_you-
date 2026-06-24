"""Report generation API routes"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

from ...modules.report_generator import ReportGenerator, ReportType, ReportFormat

router = APIRouter()

class ReportRequest(BaseModel):
    project_id: str
    project_name: str
    report_type: str = "comprehensive"
    output_format: str = "pdf"
    include_charts: bool = True

@router.post("/generate")
async def generate_report(request: ReportRequest):
    """Generate a report for a project"""
    
    try:
        report_type = ReportType(request.report_type)
        output_format = ReportFormat(request.output_format)
    except ValueError:
        raise HTTPException(400, f"Invalid report type or format")
    
    # Sample analysis data
    data = {
        "overall_score": 72.5,
        "scores": {
            "architecture": 85.0,
            "innovation": 78.0,
            "hackathon_readiness": 72.0,
            "technical_debt": 25.0,
            "team_readiness": 80.0,
            "competitive_advantage": 70.0,
        },
        "architectural_patterns": ["Microservices", "Event-Driven", "CQRS"],
        "strengths": [
            "Strong architectural foundation with clean separation of concerns",
            "High innovation potential with unique approach to problem-solving",
            "Active development with regular commits and contributions",
        ],
        "weak_spots": [
            {"area": "Testing", "title": "Insufficient Test Coverage", "severity": "high"},
            {"area": "Documentation", "title": "Missing API Documentation", "severity": "medium"},
        ],
        "recommendations": [
            "Increase test coverage to at least 60%",
            "Create comprehensive API documentation",
            "Address technical debt in core modules",
            "Prepare for judge simulation with Q&A practice",
        ],
    }
    
    generator = ReportGenerator()
    filename = await generator.generate_report(
        report_type=report_type,
        data=data,
        project_name=request.project_name,
        output_format=output_format,
        include_charts=request.include_charts,
    )
    
    return {
        "success": True,
        "filename": filename,
        "report_type": request.report_type,
        "format": request.output_format,
    }

@router.get("/templates")
async def list_report_templates():
    """List available report templates"""
    return {
        "templates": [
            {"type": "executive", "name": "Executive Summary", "description": "High-level overview for stakeholders"},
            {"type": "technical", "name": "Technical Analysis", "description": "Deep technical analysis for engineers"},
            {"type": "hackathon", "name": "Hackathon Readiness", "description": "Hackathon preparation and readiness score"},
            {"type": "competitive", "name": "Competitive Intelligence", "description": "Market and competitor analysis"},
            {"type": "architecture", "name": "Architecture Audit", "description": "Architecture review and risk assessment"},
            {"type": "comprehensive", "name": "Comprehensive Analysis", "description": "Complete project analysis report"},
        ]
    }
