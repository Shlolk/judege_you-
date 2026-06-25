import logging
from typing import List, Optional
from datetime import datetime

from core.models.project import Project

logger = logging.getLogger(__name__)


class ProjectRepository:
    def __init__(self, db_session=None):
        self.db_session = db_session

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        if self.db_session:
            from sqlalchemy import select
            from database.models import ProjectModel
            result = await self.db_session.execute(
                select(ProjectModel).where(ProjectModel.id == project_id))
            model = result.scalar_one_or_none()
            if model:
                return Project(id=model.id, name=model.name, description=model.description or "",
                               repository_url=model.repository_url, path=model.local_path,
                               created_at=model.created_at, status=model.status,
                               analysis_score=model.analysis_score, health_score=model.health_score)
        return None

    async def get_all(self) -> List[Project]:
        if self.db_session:
            from sqlalchemy import select
            from database.models import ProjectModel
            result = await self.db_session.execute(select(ProjectModel))
            models = result.scalars().all()
            return [Project(id=m.id, name=m.name, description=m.description or "",
                            repository_url=m.repository_url, path=m.local_path,
                            created_at=m.created_at, status=m.status) for m in models]
        return []

    async def save(self, project: Project) -> None:
        if self.db_session:
            from database.models import ProjectModel
            model = ProjectModel(id=project.id, name=project.name, description=project.description,
                                 repository_url=project.repository_url,
                                 local_path=project.path, status=project.status,
                                 analysis_score=project.analysis_score,
                                 health_score=project.health_score)
            self.db_session.add(model)
            await self.db_session.commit()
        else:
            logger.info(f"[Mock] Saved project {project.id}: {project.name}")

    async def update(self, project: Project) -> None:
        if self.db_session:
            from sqlalchemy import update
            from database.models import ProjectModel
            await self.db_session.execute(
                update(ProjectModel).where(ProjectModel.id == project.id)
                .values(name=project.name, description=project.description, status=project.status,
                        analysis_score=project.analysis_score, health_score=project.health_score))
            await self.db_session.commit()
        else:
            logger.info(f"[Mock] Updated project {project.id}")

    async def delete(self, project_id: str) -> None:
        if self.db_session:
            from sqlalchemy import delete
            from database.models import ProjectModel
            await self.db_session.execute(delete(ProjectModel).where(ProjectModel.id == project_id))
            await self.db_session.commit()
        else:
            logger.info(f"[Mock] Deleted project {project_id}")
