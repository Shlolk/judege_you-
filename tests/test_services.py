"""Tests for core analysis and project services"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestProjectAnalysisResult:
    """Test the core analysis result dataclass"""

    def test_overall_score_calculation(self):
        """Test overall score is correctly averaged"""
        from core.services.analysis_service import ProjectAnalysisResult

        result = ProjectAnalysisResult(
            project_id="test-1",
            architecture_score=80.0,
            innovation_score=70.0,
            technical_debt_score=20.0,
            hackathon_readiness_score=75.0,
            team_readiness_score=85.0,
            competitive_advantage_score=90.0,
        )
        # Overall = average of [80, 70, 80, 75, 85, 90]
        assert result.overall_score == pytest.approx(80.0, rel=0.1)
        # Default risk_level is "medium" (not auto-computed; done by service._risk_level)
        assert result.risk_level == "medium"

    def test_overall_score_all_zeros(self):
        """Test score with all zeros"""
        from core.services.analysis_service import ProjectAnalysisResult

        result = ProjectAnalysisResult(project_id="test-zero")
        assert result.overall_score == pytest.approx(16.67, rel=0.1)
        assert result.risk_level == "medium"

    def test_weak_points_via_service(self):
        """Test weak points from service._weak_points"""
        from core.services.analysis_service import AnalysisService, ProjectAnalysisResult

        service = AnalysisService()
        result = ProjectAnalysisResult(
            project_id="test-weak",
            architecture_score=50.0,
            technical_debt_score=80.0,
            team_readiness_score=40.0,
        )
        weak = service._weak_points(result)
        assert "Architecture complexity needs attention" in weak
        assert "Technical debt requires refactoring" in weak
        assert "Team skill gaps identified" in weak

    def test_strengths_via_service(self):
        """Test strengths from service._strength_points"""
        from core.services.analysis_service import AnalysisService, ProjectAnalysisResult

        service = AnalysisService()
        result = ProjectAnalysisResult(
            project_id="test-strong",
            architecture_score=90.0,
            innovation_score=95.0,
            team_readiness_score=88.0,
            competitive_advantage_score=92.0,
            hackathon_readiness_score=85.0,
        )
        strengths = service._strength_points(result)
        assert "Robust and scalable architecture" in strengths
        assert "Strong innovation potential" in strengths
        assert "Strong competitive advantage" in strengths

    def test_recommendations_via_service(self):
        """Test recommendations from service._recommendations"""
        from core.services.analysis_service import AnalysisService, ProjectAnalysisResult

        service = AnalysisService()
        result = ProjectAnalysisResult(
            project_id="test-rec",
            architecture_score=55.0,
            technical_debt_score=60.0,
            team_readiness_score=50.0,
        )
        recs = service._recommendations(result)
        texts = [r.lower() for r in recs]
        assert any("refactor" in t for t in texts)
        assert any("debt" in t for t in texts)
        assert any("team" in t or "skill" in t for t in texts)

    def test_default_values(self):
        """Test default values for optional fields"""
        from core.services.analysis_service import ProjectAnalysisResult

        result = ProjectAnalysisResult(project_id="test-defaults")
        assert result.weak_points == []
        assert result.strength_points == []
        assert result.recommendations == []
        assert result.market_position == {}
        assert result.created_at is not None


class TestAnalysisService:
    """Test the analysis service"""

    @pytest.mark.asyncio
    async def test_analyze_project_returns_result(self, project_from_fixture):
        """Test analyze_project returns a ProjectAnalysisResult"""
        from core.services.analysis_service import AnalysisService

        service = AnalysisService()
        result = await service.analyze_project(project_from_fixture.id)
        assert result.project_id == project_from_fixture.id
        assert isinstance(result.architecture_score, float)

    @pytest.mark.asyncio
    async def test_analyze_with_types(self, project_from_fixture):
        """Test analyze with specific analysis types"""
        from core.services.analysis_service import AnalysisService

        service = AnalysisService()
        result = await service.analyze_project(
            project_from_fixture.id,
            analysis_types=["architecture", "hackathon"],
        )
        assert result.architecture_score > 0
        assert result.hackathon_readiness_score > 0
        assert result.innovation_score == 0.0

    @pytest.mark.asyncio
    async def test_analyze_logs_warning_without_repo(self, project_from_fixture):
        """Test analyze_project works without repository"""
        from core.services.analysis_service import AnalysisService

        service = AnalysisService()
        result = await service.analyze_project(project_from_fixture.id)
        assert result.project_id == project_from_fixture.id
        assert result.architecture_score > 0

    @pytest.mark.asyncio
    async def test_risk_levels(self):
        """Test risk level thresholds"""
        from core.services.analysis_service import AnalysisService
        service = AnalysisService()

        assert service._risk_level(85) == "low"
        assert service._risk_level(70) == "medium"
        assert service._risk_level(55) == "high"
        assert service._risk_level(40) == "critical"


class TestProjectService:
    """Test the project service"""

    @pytest.mark.asyncio
    async def test_create_project(self):
        """Test project creation"""
        from core.services.project_service import ProjectService

        service = ProjectService()
        project = await service.create_project(
            name="Test Service Project",
            description="Created by service test",
        )
        assert project.name == "Test Service Project"
        assert project.id is not None

    @pytest.mark.asyncio
    async def test_get_project_returns_none_for_missing(self):
        """Test getting non-existent project"""
        from core.services.project_service import ProjectService

        service = ProjectService()
        project = await service.get_project("non-existent-id")
        assert project is None

    @pytest.mark.asyncio
    async def test_add_team_member_with_mocked_repo(self):
        """Test adding team members with mocked team repository"""
        from core.services.project_service import ProjectService

        mock_repo = MagicMock()
        mock_repo.get_by_project_id = AsyncMock(return_value=None)
        mock_repo.save = AsyncMock()

        service = ProjectService(team_repository=mock_repo)
        team = await service.add_team_member(
            project_id="test-project",
            name="Test Member",
            role="developer",
            experience_level="senior",
            skills=["Python", "Docker"],
        )
        assert len(team.members) == 1
        assert team.members[0].name == "Test Member"

    @pytest.mark.asyncio
    async def test_get_team_readiness_default(self):
        """Test team readiness with no team (returns error dict)"""
        from core.services.project_service import ProjectService

        service = ProjectService()
        readiness = await service.get_team_readiness("non-existent-id")
        assert readiness["overall_readiness"] == 50.0
        assert "error" in readiness
