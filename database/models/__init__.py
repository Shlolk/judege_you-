from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, declared_attr
from datetime import datetime
import uuid
import enum

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class AnalysisType(str, enum.Enum):
    ARCHITECTURE = "architecture"
    HACKATHON_READINESS = "hackathon_readiness"
    INNOVATION = "innovation"
    TECHNICAL_DEBT = "technical_debt"
    TEAM_READINESS = "team_readiness"
    COMPETITIVE = "competitive"
    COMPREHENSIVE = "comprehensive"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Models

class ProjectModel(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    repository_url = Column(String(500), nullable=True)
    github_owner = Column(String(255), nullable=True)
    github_repo = Column(String(255), nullable=True)
    local_path = Column(String(500), nullable=True)
    status = Column(String(50), default=ProjectStatus.ACTIVE.value, nullable=False)
    analysis_score = Column(Float, nullable=True)
    health_score = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    # Relationships
    analysis_results = relationship("AnalysisResultModel", back_populates="project", cascade="all, delete-orphan")
    team_members = relationship("TeamMemberModel", back_populates="project", cascade="all, delete-orphan")
    metrics = relationship("ProjectMetricModel", back_populates="project", cascade="all, delete-orphan")
    knowledge_entries = relationship("KnowledgeBaseEntryModel", back_populates="project", cascade="all, delete-orphan")

class AnalysisResultModel(Base, TimestampMixin):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(100), nullable=False, index=True)
    score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    weak_points = Column(JSON, nullable=True)
    strength_points = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="analysis_results")

class TeamMemberModel(Base, TimestampMixin):
    __tablename__ = "team_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    experience_level = Column(String(50), nullable=False)
    skills = Column(JSON, nullable=True)
    availability_hours_per_week = Column(Integer, default=40)
    expertise_score = Column(Float, nullable=True)
    influence_score = Column(Float, nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="team_members")

class ProjectMetricModel(Base, TimestampMixin):
    __tablename__ = "project_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="metrics")

class KnowledgeBaseEntryModel(Base, TimestampMixin):
    __tablename__ = "knowledge_base_entries"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=True)
    source_urls = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="knowledge_entries")

class CompetitorIntelligenceModel(Base, TimestampMixin):
    __tablename__ = "competitor_intelligence"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    competitor_name = Column(String(255), nullable=False)
    competitor_project = Column(String(255), nullable=False)
    market_position_score = Column(Float, nullable=True)
    similarity_score = Column(Float, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=True)

class StrategyPlanModel(Base, TimestampMixin):
    __tablename__ = "strategy_plans"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    quarter = Column(String(20), nullable=False)
    goals = Column(JSON, nullable=True)
    resource_allocation = Column(JSON, nullable=True)
    risk_mitigation = Column(JSON, nullable=True)
    key_metrics = Column(JSON, nullable=True)

class SimulationSessionModel(Base, TimestampMixin):
    __tablename__ = "simulation_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type = Column(String(50), nullable=False)  # judge, interview, defense
    status = Column(String(50), default="in_progress")
    questions = Column(JSON, nullable=True)
    answers = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(JSON, nullable=True)
    completed_at = Column(DateTime, nullable=True)
