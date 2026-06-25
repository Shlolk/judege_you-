"""Tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, fastapi_client):
        """Test GET /health returns healthy status"""
        response = fastapi_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "PROJECT WARROOM"

    def test_root_endpoint(self, fastapi_client):
        """Test GET / returns API info"""
        response = fastapi_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "PROJECT WARROOM"
        assert "docs" in data


class TestProjectEndpoints:
    """Test project CRUD endpoints"""

    def test_create_project(self, fastapi_client):
        """Test POST /api/v1/projects/ creates a project"""
        response = fastapi_client.post("/api/v1/projects/", json={
            "name": "Test API Project",
            "description": "Test project created via API",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test API Project"
        assert data["status"] == "active"
        assert "id" in data

    def test_create_project_with_repo(self, fastapi_client):
        """Test creating project with repository URL"""
        response = fastapi_client.post("/api/v1/projects/", json={
            "name": "Repo Project",
            "description": "Project with repo",
            "repository_url": "https://github.com/test/repo",
        })
        assert response.status_code == 200

    def test_get_project(self, fastapi_client):
        """Test GET /api/v1/projects/{id} returns project"""
        response = fastapi_client.get("/api/v1/projects/test-id")
        assert response.status_code == 200
        assert "id" in response.json()

    def test_scan_endpoint_no_path(self, fastapi_client):
        """Test POST /api/v1/projects/scan without path returns error"""
        response = fastapi_client.post("/api/v1/projects/scan", params={"path": ""})
        # Should return 400 or 422 for invalid path
        assert response.status_code in (400, 422)

    def test_clone_endpoint_missing_url(self, fastapi_client):
        """Test POST /api/v1/projects/clone without URL"""
        response = fastapi_client.post("/api/v1/projects/clone", params={"repo_url": ""})
        assert response.status_code in (400, 422)


class TestAnalysisEndpoints:
    """Test analysis endpoints"""

    def test_analyze_endpoint(self, fastapi_client):
        """Test POST /api/v1/analysis/analyze runs analysis"""
        response = fastapi_client.post("/api/v1/analysis/analyze", json={
            "project_id": "test-analysis-1",
            "project_name": "Analysis Test",
            "project_description": "Test project for API analysis",
            "analysis_types": ["architecture", "hackathon"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "test-analysis-1"
        assert data["overall_score"] > 0
        assert "architecture" in str(data["scores"]).lower()

    def test_architecture_analysis_endpoint(self, fastapi_client):
        """Test POST /api/v1/analysis/architecture"""
        response = fastapi_client.post("/api/v1/analysis/architecture", params={
            "project_id": "arch-test",
            "project_name": "Arch Test",
            "project_description": "Architecture analysis test",
        })
        assert response.status_code == 200
        data = response.json()
        assert "architecture_score" in data
        assert "risk_level" in data

    def test_hackathon_readiness_endpoint(self, fastapi_client):
        """Test POST /api/v1/analysis/hackathon-readiness"""
        response = fastapi_client.post("/api/v1/analysis/hackathon-readiness", params={
            "project_id": "hack-test",
            "project_name": "Hack Test",
            "project_description": "Hackathon readiness test",
        })
        assert response.status_code == 200
        data = response.json()
        assert "winning_probability" in data
        assert "competition_level" in data

    def test_get_scores(self, fastapi_client):
        """Test GET /api/v1/analysis/{id}/scores"""
        response = fastapi_client.get("/api/v1/analysis/test-id/scores")
        assert response.status_code == 200
        data = response.json()
        assert "scores" in data
        assert "overall" in data


class TestSimulationEndpoints:
    """Test simulation endpoints"""

    def test_judge_simulation(self, fastapi_client):
        """Test POST /api/v1/simulation/judge"""
        response = fastapi_client.post("/api/v1/simulation/judge", json={
            "project_id": "judge-test",
            "project_name": "Judge Test",
            "project_description": "Judge simulation test",
            "persona": "sih_judge",
            "mode": "moderate",
            "num_questions": 3,
        })
        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "final_verdict" in data

    def test_interview_simulation(self, fastapi_client):
        """Test POST /api/v1/simulation/interview"""
        response = fastapi_client.post("/api/v1/simulation/interview", json={
            "project_id": "interview-test",
            "project_name": "Interview Test",
            "project_description": "Interview simulation test",
            "interview_type": "technical",
            "difficulty": "mid",
            "num_questions": 3,
        })
        assert response.status_code == 200
        data = response.json()
        assert "readiness_level" in data
        assert "recommendations" in data

    def test_cross_examination(self, fastapi_client):
        """Test POST /api/v1/simulation/cross-examination"""
        response = fastapi_client.post(
            "/api/v1/simulation/cross-examination",
            params={
                "project_id": "cross-test",
                "project_name": "Cross Test",
                "project_description": "Cross examination test",
                "num_rounds": 2,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "rounds" in data
        assert "critical_findings" in data


class TestReportEndpoints:
    """Test report generation endpoints"""

    def test_generate_report(self, fastapi_client):
        """Test POST /api/v1/reports/generate"""
        response = fastapi_client.post("/api/v1/reports/generate", json={
            "project_id": "report-test",
            "project_name": "Report Test",
            "report_type": "executive",
            "output_format": "json",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "filename" in data

    def test_list_templates(self, fastapi_client):
        """Test GET /api/v1/reports/templates"""
        response = fastapi_client.get("/api/v1/reports/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0


class TestCompetitiveEndpoints:
    """Test competitive analysis endpoints"""

    def test_competitive_analysis(self, fastapi_client):
        """Test POST /api/v1/competitive/analyze"""
        response = fastapi_client.post("/api/v1/competitive/analyze", json={
            "project_name": "Comp Test",
            "project_description": "Competitive analysis test",
        })
        assert response.status_code == 200
        data = response.json()
        assert "overall_position" in data
        assert "strategic_recommendations" in data
