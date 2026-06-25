import logging
from typing import List, Optional

from core.models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


class AnalysisRepository:
    def __init__(self, db_session=None):
        self.db_session = db_session

    async def get_by_project_id(self, project_id: str) -> List[AnalysisResult]:
        if self.db_session:
            from sqlalchemy import select
            from database.models import AnalysisResultModel
            result = await self.db_session.execute(
                select(AnalysisResultModel).where(AnalysisResultModel.project_id == project_id))
            models = result.scalars().all()
            return [AnalysisResult(id=m.id, project_id=m.project_id,
                                   analysis_type=m.analysis_type, score=m.score,
                                   details=m.details or {}, recommendations=m.recommendations or [],
                                   created_at=m.created_at) for m in models]
        return []

    async def save(self, project_id: str, analysis_result: AnalysisResult) -> None:
        if self.db_session:
            from database.models import AnalysisResultModel
            model = AnalysisResultModel(id=analysis_result.id, project_id=project_id,
                                        analysis_type=analysis_result.analysis_type,
                                        score=analysis_result.score,
                                        details=analysis_result.details,
                                        recommendations=analysis_result.recommendations)
            self.db_session.add(model)
            await self.db_session.commit()
        else:
            logger.info(f"[Mock] Saved analysis for project {project_id}: {analysis_result.analysis_type} = {analysis_result.score}")

    async def get_latest(self, project_id: str, analysis_type: str = None) -> Optional[AnalysisResult]:
        if self.db_session:
            from sqlalchemy import select, desc
            from database.models import AnalysisResultModel
            query = select(AnalysisResultModel).where(AnalysisResultModel.project_id == project_id)
            if analysis_type:
                query = query.where(AnalysisResultModel.analysis_type == analysis_type)
            query = query.order_by(desc(AnalysisResultModel.created_at)).limit(1)
            result = await self.db_session.execute(query)
            model = result.scalar_one_or_none()
            if model:
                return AnalysisResult(id=model.id, project_id=model.project_id,
                                      analysis_type=model.analysis_type, score=model.score,
                                      details=model.details or {}, recommendations=model.recommendations or [],
                                      created_at=model.created_at)
        return None
