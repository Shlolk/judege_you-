import logging
from collections import Counter
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime

from ..models.project import Project

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, project_repository=None, analysis_repository=None,
                 team_repository=None, analyzer_service=None):
        self.project_repository = project_repository
        self.analysis_repository = analysis_repository
        self.team_repository = team_repository
        self.analyzer_service = analyzer_service

    async def create_project(self, name: str, description: str,
                             repository_url: Optional[str] = None,
                             github_owner: Optional[str] = None,
                             github_repo: Optional[str] = None,
                             path: Optional[str] = None) -> Project:
        project = Project.create(name=name, description=description,
                                 repository_url=repository_url,
                                 github_owner=github_owner,
                                 github_repo=github_repo, path=path)
        if self.project_repository:
            await self.project_repository.save(project)
        else:
            logger.warning("No project_repository available, project not persisted")
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        if self.project_repository:
            return await self.project_repository.get_by_id(project_id)
        return None

    async def get_all_projects(self) -> List[Project]:
        if self.project_repository:
            return await self.project_repository.get_all()
        return []

    async def analyze_project(self, project_id: str,
                              analysis_types: Optional[List[str]] = None) -> Dict[str, Any]:
        if not self.analyzer_service:
            return {"error": "Analyzer service not available"}
        result = await self.analyzer_service.analyze_project(project_id, analysis_types)
        project = await self.get_project(project_id)
        return {"project": project, "analysis": result}

    async def add_team_member(self, project_id: str, name: str, role: str,
                              experience_level: str, skills: List[str]) -> Any:
        from ..models.team import Team, TeamMember
        if not self.team_repository:
            return {"error": "Team repository not available"}

        team = await self.team_repository.get_by_project_id(project_id)
        if not team:
            team = Team.create(project_id=project_id)

        member = TeamMember(id=str(uuid4()), name=name, role=role,
                            experience_level=experience_level, skills=skills)
        team.add_member(member)
        await self.team_repository.save(team)
        return team

    async def get_team_readiness(self, project_id: str) -> Dict[str, Any]:
        if not self.team_repository:
            return {"overall_readiness": 50.0, "error": "Team repository not available"}

        team = await self.team_repository.get_by_project_id(project_id)
        if not team or not team.members:
            return {"overall_readiness": 50.0, "recommendations": ["Add team members"]}

        all_skills = [s for m in team.members for s in m.skills]
        skill_counts = Counter(all_skills)
        senior_count = sum(1 for m in team.members if m.experience_level == "senior")

        readiness = (min(1.0, len(skill_counts) / (len(team.members) * 3)) * 30 +
                     (senior_count / max(1, len(team.members))) * 40 +
                     (min(1.0, len(team.members) / 5)) * 30)

        return {"overall_readiness": readiness * 100,
                "skills_analysis": dict(skill_counts.most_common()),
                "team_size": len(team.members), "senior_members": senior_count,
                "recommendations": self._team_recs(team)}

    def _team_recs(self, team: Any) -> List[str]:
        recs = []
        if len(team.members) < 2:
            recs.append("Add more team members for collaboration")
        from collections import Counter
        all_skills = [s for m in team.members for s in m.skills]
        if len(Counter(all_skills)) < 5:
            recs.append("Increase skill diversity")
        if not any(m.experience_level == "senior" for m in team.members):
            recs.append("Add senior team members for guidance")
        return recs or ["Team is well-balanced"]
