from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

@dataclass
class Project:
    id: str
    name: str
    description: str
    repository_url: Optional[str] = None
    github_owner: Optional[str] = None
    github_repo: Optional[str] = None
    path: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    status: str = "active"
    analysis_score: Optional[float] = None
    health_score: Optional[float] = None
    metadata: Optional[dict] = None
    archived_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def create(cls, name: str, description: str, repository_url: Optional[str] = None,
               github_owner: Optional[str] = None, github_repo: Optional[str] = None,
               path: Optional[str] = None) -> "Project":
        return cls(id=str(uuid4()), name=name, description=description,
                   repository_url=repository_url, github_owner=github_owner,
                   github_repo=github_repo, path=path,
                   created_at=datetime.now())

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
