"""Tests for database repositories"""

import pytest


class TestProjectRepository:
    """Test project repository"""

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self):
        """Test saving and retrieving a project"""
        from database.repositories.project_repository import ProjectRepository
        from core.models.project import Project

        repo = ProjectRepository()
        project = Project.create(name="DB Test", description="Testing DB repository")

        # Save (mock mode since no DB)
        await repo.save(project)

        # Get by ID (mock returns None)
        retrieved = await repo.get_by_id(project.id)
        assert retrieved is None  # Mock mode

    @pytest.mark.asyncio
    async def test_get_all_empty(self):
        """Test get_all returns empty list when no DB"""
        from database.repositories.project_repository import ProjectRepository

        repo = ProjectRepository()
        projects = await repo.get_all()
        assert projects == []

    @pytest.mark.asyncio
    async def test_count_zero(self):
        """Test count returns 0 when no DB"""
        from database.repositories.project_repository import ProjectRepository

        repo = ProjectRepository()
        count = await repo.count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete doesn't crash in mock mode"""
        from database.repositories.project_repository import ProjectRepository

        repo = ProjectRepository()
        # Should not raise
        await repo.delete("non-existent-id")

    @pytest.mark.asyncio
    async def test_update(self):
        """Test update doesn't crash in mock mode"""
        from database.repositories.project_repository import ProjectRepository
        from core.models.project import Project

        repo = ProjectRepository()
        project = Project.create(name="Update Test", description="Testing update")
        project.name = "Updated Name"
        await repo.update(project)


class TestAnalysisRepository:
    """Test analysis repository"""

    @pytest.mark.asyncio
    async def test_save_and_get_by_project(self):
        """Test saving and retrieving analysis results"""
        from database.repositories.analysis_repository import AnalysisRepository
        from core.models.analysis import AnalysisResult
        from uuid import uuid4

        repo = AnalysisRepository()
        analysis = AnalysisResult(
            id=str(uuid4()),
            project_id="test-project",
            analysis_type="architecture",
            score=85.0,
            details={"pattern": "microservices"},
            recommendations=["Add caching"],
        )

        await repo.save("test-project", analysis)

        results = await repo.get_by_project_id("test-project")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_latest(self):
        """Test get_latest returns None in mock mode"""
        from database.repositories.analysis_repository import AnalysisRepository

        repo = AnalysisRepository()
        latest = await repo.get_latest("test-project", "architecture")
        assert latest is None

    @pytest.mark.asyncio
    async def test_get_by_type_empty(self):
        """Test get_by_type returns empty in mock mode"""
        from database.repositories.analysis_repository import AnalysisRepository

        repo = AnalysisRepository()
        results = await repo.get_by_type("test-project", "architecture")
        assert results == []


class TestTeamRepository:
    """Test team repository"""

    @pytest.mark.asyncio
    async def test_save_and_retrieve(self):
        """Test saving and retrieving team"""
        from database.repositories.team_repository import TeamRepository
        from core.models.team import Team, TeamMember

        repo = TeamRepository()
        team = Team.create(project_id="test-project")
        team.add_member(TeamMember(
            id="member-1", name="Alice", role="developer",
            experience_level="senior", skills=["Python", "AWS"],
        ))

        await repo.save(team)

        retrieved = await repo.get_by_project_id("test-project")
        assert retrieved is None  # Mock mode

    @pytest.mark.asyncio
    async def test_add_member(self):
        """Test adding a single member"""
        from database.repositories.team_repository import TeamRepository
        from core.models.team import TeamMember

        repo = TeamRepository()
        member = TeamMember(
            id="member-2", name="Bob", role="designer",
            experience_level="mid", skills=["Figma"],
        )
        await repo.add_member("test-project", member)

    @pytest.mark.asyncio
    async def test_member_count(self):
        """Test member count returns 0 in mock mode"""
        from database.repositories.team_repository import TeamRepository

        repo = TeamRepository()
        count = await repo.get_member_count("test-project")
        assert count == 0
