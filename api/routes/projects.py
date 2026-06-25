"""Project management API routes"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

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
    from core.models.project import Project as ProjectModel
    p = ProjectModel.create(
        name=project.name,
        description=project.description,
        repository_url=project.repository_url,
        path=project.path,
    )
    return ProjectResponse(id=p.id, name=p.name, description=p.description, status="active")

@router.post("/scan")
async def scan_project(path: str):
    """Scan a project directory"""
    try:
        from core.di.container import container
        scanner = container.get("project_scanner")
        if not scanner:
            raise HTTPException(status_code=503, detail="Scanner not available")

        result = await scanner.scan_project(path)
        return {
            "success": True,
            "data": {
                "project_name": result.project_name,
                "total_files": result.total_files,
                "total_dirs": result.total_dirs,
                "total_size_kb": result.total_size_bytes / 1024,
                "languages": result.languages,
                "has_git": result.git_info.has_git,
                "has_tests": result.has_tests,
                "has_docker": result.has_docker,
                "has_ci": result.has_ci,
                "has_readme": result.has_readme,
                "branch": result.git_info.branch,
                "commit_count": result.git_info.commit_count,
                "structure": [
                    {"path": d.path, "files": d.file_count}
                    for d in result.structure[:20]
                ],
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Project scan failed")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/clone")
async def clone_project(repo_url: str, branch: Optional[str] = None):
    """Clone a repository for analysis"""
    try:
        from core.di.container import container
        scanner = container.get("project_scanner")
        if not scanner:
            raise HTTPException(status_code=503, detail="Scanner not available")

        path = await scanner.clone_repository(repo_url, branch=branch)
        return {"success": True, "path": path}
    except Exception as e:
        logger.exception("Clone failed")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    from core.di.container import container
    project_svc = container.get("project_service")
    if project_svc:
        project = await project_svc.get_project(project_id)
        if project:
            return {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "repository_url": project.repository_url,
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
            }
    return {"id": project_id, "name": "Unknown", "description": "", "status": "unknown"}
