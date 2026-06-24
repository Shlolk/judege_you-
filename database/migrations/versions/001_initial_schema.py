"""Initial database migration for PROJECT WARROOM

Revision ID: 001
Revises:
Create Date: 2024-06-23 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create initial database schema"""
    
    # Projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("repository_url", sa.String(500), nullable=True),
        sa.Column("github_owner", sa.String(255), nullable=True),
        sa.Column("github_repo", sa.String(255), nullable=True),
        sa.Column("local_path", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("analysis_score", sa.Float, nullable=True),
        sa.Column("health_score", sa.Float, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.func.now()),
        sa.Column("archived_at", sa.DateTime, nullable=True),
    )

    # Analysis results table
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("analysis_type", sa.String(100), nullable=False, index=True),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("recommendations", postgresql.JSONB, nullable=True),
        sa.Column("weak_points", postgresql.JSONB, nullable=True),
        sa.Column("strength_points", postgresql.JSONB, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Team members table
    op.create_table(
        "team_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("experience_level", sa.String(50), nullable=False),
        sa.Column("skills", postgresql.JSONB, nullable=True),
        sa.Column("availability_hours_per_week", sa.Integer, server_default="40"),
        sa.Column("expertise_score", sa.Float, nullable=True),
        sa.Column("influence_score", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Project metrics table
    op.create_table(
        "project_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric_type", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Float, nullable=False),
        sa.Column("metric_unit", sa.String(50), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Knowledge base entries table
    op.create_table(
        "knowledge_base_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entry_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("source_urls", postgresql.JSONB, nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Competitor intelligence table
    op.create_table(
        "competitor_intelligence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("competitor_name", sa.String(255), nullable=False),
        sa.Column("competitor_project", sa.String(255), nullable=False),
        sa.Column("market_position_score", sa.Float, nullable=True),
        sa.Column("similarity_score", sa.Float, nullable=True),
        sa.Column("strengths", postgresql.JSONB, nullable=True),
        sa.Column("weaknesses", postgresql.JSONB, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("last_updated", sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Simulation sessions table
    op.create_table(
        "simulation_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("session_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="in_progress"),
        sa.Column("questions", postgresql.JSONB, nullable=True),
        sa.Column("answers", postgresql.JSONB, nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("feedback", postgresql.JSONB, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Create indexes
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_name_lower", "projects", [sa.text("LOWER(name)")])
    op.create_index("ix_analysis_project_type", "analysis_results", ["project_id", "analysis_type"])
    op.create_index("ix_metrics_project_type", "project_metrics", ["project_id", "metric_type"])
    op.create_index("ix_simulation_project_type", "simulation_sessions", ["project_id", "session_type"])

def downgrade() -> None:
    """Drop all tables"""
    op.drop_table("simulation_sessions")
    op.drop_table("competitor_intelligence")
    op.drop_table("knowledge_base_entries")
    op.drop_table("project_metrics")
    op.drop_table("team_members")
    op.drop_table("analysis_results")
    op.drop_table("projects")
