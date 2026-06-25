import logging
from typing import List, Optional

from core.models.team import Team, TeamMember

logger = logging.getLogger(__name__)


class TeamRepository:
    def __init__(self, db_session=None):
        self.db_session = db_session

    async def get_by_project_id(self, project_id: str) -> Optional[Team]:
        if self.db_session:
            from sqlalchemy import select
            from database.models import TeamMemberModel
            result = await self.db_session.execute(
                select(TeamMemberModel).where(TeamMemberModel.project_id == project_id))
            models = result.scalars().all()
            if models:
                members = [TeamMember(id=m.id, name=m.name, role=m.role,
                                      experience_level=m.experience_level,
                                      skills=m.skills or [],
                                      availability_hours_per_week=m.availability_hours_per_week)
                           for m in models]
                return Team(id="team_" + project_id, project_id=project_id, members=members)
        return None

    async def save(self, team: Team) -> None:
        if self.db_session:
            from database.models import TeamMemberModel
            for member in team.members:
                model = TeamMemberModel(id=member.id, project_id=team.project_id,
                                        name=member.name, role=member.role,
                                        experience_level=member.experience_level,
                                        skills=member.skills,
                                        availability_hours_per_week=member.availability_hours_per_week,
                                        expertise_score=member.expertise_score,
                                        influence_score=member.influence_score)
                self.db_session.add(model)
            await self.db_session.commit()
        else:
            logger.info(f"[Mock] Saved team for project {team.project_id}: {len(team.members)} members")

    async def update(self, team: Team) -> None:
        logger.info(f"[Mock] Updated team for project {team.project_id}")

    async def delete(self, team_id: str) -> None:
        logger.info(f"[Mock] Deleted team {team_id}")
