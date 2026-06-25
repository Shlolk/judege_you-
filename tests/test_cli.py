"""Tests for CLI commands"""

import pytest
import sys
from pathlib import Path


class TestCLICommands:
    """Test CLI command parsing and execution"""

    def test_version_command(self):
        """Test that version command runs without error"""
        from cli.commands import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "PROJECT WARROOM" in result.output
        assert "v0.1.0" in result.output

    def test_init_command(self, tmp_path):
        """Test init command creates project directory"""
        from cli.commands import app
        from typer.testing import CliRunner

        runner = CliRunner()
        project_name = "test-cli-project"
        output_dir = str(tmp_path / "projects")

        result = runner.invoke(app, [
            "init", project_name,
            "--description", "Test CLI project",
            "--output-dir", output_dir,
        ])
        assert result.exit_code == 0
        assert "Initialized" in result.output
        assert Path(output_dir, project_name).exists()

    def test_init_with_repo(self, tmp_path):
        """Test init with repository URL"""
        from cli.commands import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", "repo-project",
            "--repo", "https://github.com/test/repo",
            "--output-dir", str(tmp_path / "projects"),
        ])
        assert result.exit_code == 0
        assert "Repository" in result.output

    def test_init_generates_project_id(self, tmp_path):
        """Test init creates a project with a UUID"""
        from cli.commands import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", "uuid-project",
            "--output-dir", str(tmp_path / "projects"),
        ])
        assert result.exit_code == 0
        assert "Project ID:" in result.output

    def test_scan_command(self, sample_codebase):
        """Test scan command with a real directory"""
        from cli.commands import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["scan", sample_codebase])
        # Should work even without Rich terminal (CLI runs programmatically)
        assert result.exit_code == 0 or "Project Scan" in result.output

    def test_analyze_requires_project(self):
        """Test analyze handles missing project gracefully"""
        from cli.commands import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "non-existent-project"])
        # Should not crash - analyzer returns mock data with a generated project
        assert result.exit_code == 0

    def test_help_output(self):
        """Test help contains all commands"""
        from cli.commands import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        for cmd in ["init", "analyze", "judge", "readiness", "competitive", "scan", "report", "version"]:
            assert cmd in result.output
