from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

@dataclass
class TeamMember:
    id: str
    name: str
    role: str
    experience_level: str
    skills: List[str]
    availability_hours_per_week: int = 40
    expertise_score: Optional[float] = None
    influence_score: Optional[float] = None

    def __post_init__(self):
        if self.expertise_score is None:
            self.expertise_score = self._calculate_expertise_score()
        if self.influence_score is None:
            self.influence_score = self._calculate_influence_score()

    def _calculate_expertise_score(self) -> float:
        weights = {"junior": 0.3, "mid": 0.6, "senior": 0.8, "lead": 1.0}
        return weights.get(self.experience_level, 0.5) * 0.7 + min(1.0, len(self.skills) / 10) * 0.3

    def _calculate_influence_score(self) -> float:
        role_w = {"developer": 0.6, "designer": 0.5, "product_manager": 0.8,
                  "technical_lead": 0.9, "architect": 1.0, "researcher": 0.7}
        exp_w = {"junior": 0.5, "mid": 0.7, "senior": 0.9, "lead": 1.0}
        return role_w.get(self.role.lower(), 0.5) * 0.6 + exp_w.get(self.experience_level, 0.5) * 0.4

@dataclass
class Team:
    id: str
    project_id: str
    members: List[TeamMember]
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @classmethod
    def create(cls, project_id: str, members: Optional[List[TeamMember]] = None) -> "Team":
        return cls(id=str(uuid4()), project_id=project_id, members=members or [], created_at=datetime.now())

    def add_member(self, member: TeamMember) -> None:
        self.members.append(member)
        self.updated_at = datetime.now()

    @property
    def total_availability_hours(self) -> int:
        return sum(m.availability_hours_per_week for m in self.members)

    @property
    def average_expertise_score(self) -> float:
        return sum(m.expertise_score for m in self.members) / len(self.members) if self.members else 0.0

    @property
    def average_influence_score(self) -> float:
        return sum(m.influence_score for m in self.members) / len(self.members) if self.members else 0.0
