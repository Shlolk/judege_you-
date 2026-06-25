"""Project management API routes"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from modules.project_scanner import ProjectScanner, ProjectScanResult

router = APIRouter()
scanner = ProjectScanner()

class ProjectCreate(BaseModel):
    name: str
    description: str
    repository_url: Optional[str] = None
    path: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    return ProjectResponse(
        id="new-project-id",
        name=project.name,
        description=project.description,
        status="active",
    )

@router.post("/scan")
async def scan_project(path: str):
    """Scan a project directory"""
    try:
        result = await scanner.scan_project(path)
        return {
            "success": True,
            "data": {
                "project_name": result.project_name,
                "total_files": result.total_files,
                "languages": result.languages,
                "has_git": result.git_info.has_git,
                "has_tests": result.has_tests,
                "has_docker": result.has_docker,
                "has_ci": result.has_ci,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/clone")
async def clone_project(repo_url: str, branch: Optional[str] = None):
    """Clone a repository for analysis"""
    try:
        path = await scanner.clone_repository(repo_url, branch=branch)
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    return {
        "id": project_id,
        "name": "Sample Project",
        "description": "A sample project for demonstration",
        "status": "active",
    }
