"""Test configuration and fixtures"""

import pytest
import asyncio
import tempfile
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_project_data():
    """Sample project data for testing"""
    return {
        "name": "Test Project",
        "description": "A sample project for testing PROJECT WARROOM analysis features. "
                        "This project demonstrates AI-powered code analysis, architecture review, "
                        "and hackathon readiness evaluation.",
        "repository_url": "https://github.com/test/project",
    }


@pytest.fixture
def sample_team_data():
    """Sample team data for testing"""
    return {
        "members": [
            {"name": "Alice", "role": "developer", "experience_level": "senior",
             "skills": ["Python", "React", "AWS", "Docker"]},
            {"name": "Bob", "role": "developer", "experience_level": "mid",
             "skills": ["Python", "FastAPI", "PostgreSQL"]},
            {"name": "Charlie", "role": "designer", "experience_level": "senior",
             "skills": ["Figma", "UI/UX", "Prototyping"]},
        ]
    }


@pytest.fixture
def sample_codebase():
    """Create a temporary sample codebase for testing scanners and parsers"""
    tmp_dir = tempfile.mkdtemp()

    files = {
        "main.py": """
import os
import sys

def main():
    print("Hello, World!")
    try:
        result = process_data(data)
        return result
    except:
        pass

def process_data(data):
    return {"status": "ok", "data": data}

if __name__ == "__main__":
    main()
""",
        "utils.py": """
import json
import requests

API_KEY = "sk-test-12345"

def fetch_data(url):
    response = requests.get(url)
    return response.json()

def transform_data(data):
    result = []
    for item in data:
        result.append(item)
    return result
""",
        "models.py": """
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: str
    name: str
    email: str
    role: str = "user"
""",
        "README.md": "# Test Project\n\nA sample project for testing PROJECT WARROOM.",
        "requirements.txt": "fastapi>=0.109.0\npytest>=7.4.0",
        "Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .",
        "tests/test_sample.py": "def test_pass():\n    assert True\n",
    }

    for filename, content in files.items():
        filepath = os.path.join(tmp_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)

    yield tmp_dir

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def project_from_fixture(sample_project_data):
    """Create a domain Project from fixture data"""
    from core.models.project import Project
    return Project.create(
        name=sample_project_data["name"],
        description=sample_project_data["description"],
        repository_url=sample_project_data["repository_url"],
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def ollaama_mock():
    """Mock Ollama client that returns predictable responses"""
    from ai.models.ollama_client import OllamaClient
    client = OllamaClient(base_url="http://localhost:99999", model="gemma3:latest")
    return client


@pytest.fixture
def fastapi_client():
    """FastAPI TestClient for API testing"""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)
