"""Project repository with SQLAlchemy async queries"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, update, delete

from core.models.project import Project
from database.models import ProjectModel
from database.config import db_config

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Repository for project CRUD operations"""

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] get_by_id({project_id})")
                return None
            result = await session.execute(
                select(ProjectModel).where(ProjectModel.id == project_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    async def get_all(self) -> List[Project]:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info("[Mock] get_all()")
                return []
            result = await session.execute(select(ProjectModel).order_by(ProjectModel.created_at.desc()))
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def save(self, project: Project) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Saved project {project.id}: {project.name}")
                return
            model = self._from_domain(project)
            session.add(model)

    async def update(self, project: Project) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Updated project {project.id}")
                return
            await session.execute(
                update(ProjectModel).where(ProjectModel.id == project.id).values(
                    name=project.name,
                    description=project.description,
                    repository_url=project.repository_url,
                    local_path=project.path,
                    status=project.status,
                    analysis_score=project.analysis_score,
                    health_score=project.health_score,
                    metadata_json=project.metadata,
                    updated_at=datetime.utcnow(),
                )
            )

    async def delete(self, project_id: str) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Deleted project {project_id}")
                return
            await session.execute(delete(ProjectModel).where(ProjectModel.id == project_id))

    async def count(self) -> int:
        async with db_config.session(self.db_session) as session:
            if session is None:
                return 0
            from sqlalchemy import func
            result = await session.execute(select(func.count()).select_from(ProjectModel))
            return result.scalar() or 0

    # --- Mappers ---

    @staticmethod
    def _to_domain(model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=model.name,
            description=model.description or "",
            repository_url=model.repository_url,
            github_owner=model.github_owner,
            github_repo=model.github_repo,
            path=model.local_path,
            created_at=model.created_at,
            updated_at=model.updated_at,
            status=model.status,
            analysis_score=model.analysis_score,
            health_score=model.health_score,
            metadata=model.metadata_json or {},
            archived_at=model.archived_at,
        )

    @staticmethod
    def _from_domain(project: Project) -> ProjectModel:
        return ProjectModel(
            id=project.id,
            name=project.name,
            description=project.description,
            repository_url=project.repository_url,
            github_owner=project.github_owner,
            github_repo=project.github_repo,
            local_path=project.path,
            status=project.status,
            analysis_score=project.analysis_score,
            health_score=project.health_score,
            metadata_json=project.metadata or {},
            archived_at=project.archived_at,
        )
