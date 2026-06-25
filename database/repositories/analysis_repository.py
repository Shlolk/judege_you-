"""Analysis result repository with SQLAlchemy async queries"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, desc

from core.models.analysis import AnalysisResult
from database.models import AnalysisResultModel
from database.config import db_config

logger = logging.getLogger(__name__)


class AnalysisRepository:
    """Repository for analysis result CRUD operations"""

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def get_by_project_id(self, project_id: str) -> List[AnalysisResult]:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] get_by_project_id({project_id})")
                return []
            result = await session.execute(
                select(AnalysisResultModel)
                .where(AnalysisResultModel.project_id == project_id)
                .order_by(AnalysisResultModel.created_at.desc())
            )
            return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, project_id: str, analysis_result: AnalysisResult) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Saved analysis for project {project_id}: {analysis_result.analysis_type} = {analysis_result.score}")
                return
            model = self._from_domain(project_id, analysis_result)
            session.add(model)

    async def get_latest(self, project_id: str, analysis_type: str = None) -> Optional[AnalysisResult]:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] get_latest({project_id}, {analysis_type})")
                return None
            query = select(AnalysisResultModel).where(AnalysisResultModel.project_id == project_id)
            if analysis_type:
                query = query.where(AnalysisResultModel.analysis_type == analysis_type)
            query = query.order_by(desc(AnalysisResultModel.created_at)).limit(1)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def get_by_type(self, project_id: str, analysis_type: str) -> List[AnalysisResult]:
        async with db_config.session(self.db_session) as session:
            if session is None:
                return []
            result = await session.execute(
                select(AnalysisResultModel)
                .where(AnalysisResultModel.project_id == project_id)
                .where(AnalysisResultModel.analysis_type == analysis_type)
                .order_by(AnalysisResultModel.created_at.desc())
            )
            return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, analysis_id: str) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Deleted analysis {analysis_id}")
                return
            from sqlalchemy import delete as sa_delete
            await session.execute(
                sa_delete(AnalysisResultModel).where(AnalysisResultModel.id == analysis_id)
            )

    # --- Mappers ---

    @staticmethod
    def _to_domain(model: AnalysisResultModel) -> AnalysisResult:
        return AnalysisResult(
            id=model.id,
            project_id=model.project_id,
            analysis_type=model.analysis_type,
            score=model.score,
            details={
                "risk_level": model.risk_level,
                "weak_points": model.weak_points or [],
                "strength_points": model.strength_points or [],
                **(model.details or {}),
            },
            recommendations=model.recommendations or [],
            created_at=model.created_at,
        )

    @staticmethod
    def _from_domain(project_id: str, domain: AnalysisResult) -> AnalysisResultModel:
        return AnalysisResultModel(
            id=domain.id,
            project_id=project_id,
            analysis_type=domain.analysis_type,
            score=domain.score,
            risk_level=domain.details.get("risk_level") if domain.details else None,
            details=domain.details,
            recommendations=domain.recommendations,
            weak_points=domain.details.get("weak_points") if domain.details else None,
            strength_points=domain.details.get("strength_points") if domain.details else None,
        )
