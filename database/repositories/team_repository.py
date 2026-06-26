"""Team repository with SQLAlchemy async queries"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select

from core.models.team import Team, TeamMember
from database.models import TeamMemberModel
from database.config import db_config

logger = logging.getLogger(__name__)


class TeamRepository:
    """Repository for team CRUD operations"""

    def __init__(self, db_session=None):
        self.db_session = db_session

    async def get_by_project_id(self, project_id: str) -> Optional[Team]:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] get_by_project_id({project_id})")
                return None
            result = await session.execute(
                select(TeamMemberModel).where(TeamMemberModel.project_id == project_id)
            )
            models = result.scalars().all()
            if not models:
                return None
            members = [self._member_to_domain(m) for m in models]
            return Team(
                id=f"team_{project_id}",
                project_id=project_id,
                members=members,
                created_at=models[0].created_at if models[0].created_at else None,
            )

    async def save(self, team: Team) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Saved team for project {team.project_id}: {len(team.members)} members")
                return
            # Delete existing members for clean save
            from sqlalchemy import delete as sa_delete
            await session.execute(
                sa_delete(TeamMemberModel).where(TeamMemberModel.project_id == team.project_id)
            )
            for member in team.members:
                model = self._member_from_domain(member, team.project_id)
                session.add(model)

    async def add_member(self, project_id: str, member: TeamMember) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Added member {member.name} to project {project_id}")
                return
            model = self._member_from_domain(member, project_id)
            session.add(model)

    async def remove_member(self, member_id: str) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Removed member {member_id}")
                return
            from sqlalchemy import delete as sa_delete
            await session.execute(
                sa_delete(TeamMemberModel).where(TeamMemberModel.id == member_id)
            )

    async def delete(self, team_id: str) -> None:
        async with db_config.session(self.db_session) as session:
            if session is None:
                logger.info(f"[Mock] Deleted team {team_id}")
                return
            from sqlalchemy import delete as sa_delete
            await session.execute(
                sa_delete(TeamMemberModel).where(TeamMemberModel.id == team_id)
            )

    async def get_member_count(self, project_id: str) -> int:
        async with db_config.session(self.db_session) as session:
            if session is None:
                return 0
            from sqlalchemy import func
            result = await session.execute(
                select(func.count()).select_from(TeamMemberModel)
                .where(TeamMemberModel.project_id == project_id)
            )
            return result.scalar() or 0

    # --- Mappers ---

    @staticmethod
    def _member_to_domain(model: TeamMemberModel) -> TeamMember:
        return TeamMember(
            id=model.id,
            name=model.name,
            role=model.role,
            experience_level=model.experience_level,
            skills=model.skills or [],
            availability_hours_per_week=model.availability_hours_per_week,
            expertise_score=model.expertise_score,
            influence_score=model.influence_score,
        )

    @staticmethod
    def _member_from_domain(member: TeamMember, project_id: str) -> TeamMemberModel:
        return TeamMemberModel(
            id=member.id,
            project_id=project_id,
            name=member.name,
            role=member.role,
            experience_level=member.experience_level,
            skills=member.skills,
            availability_hours_per_week=member.availability_hours_per_week,
            expertise_score=member.expertise_score,
            influence_score=member.influence_score,
        )
