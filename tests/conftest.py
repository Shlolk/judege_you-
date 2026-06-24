"""Test configuration and fixtures"""

import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def sample_project_data():
    """Sample project data for testing"""
    return {
        "name": "Test Project",
        "description": "A sample project for testing PROJECT WARROOM analysis features",
        "repository_url": "https://github.com/test/project",
    }

@pytest.fixture
def sample_team_data():
    """Sample team data for testing"""
    return {
        "members": [
            {"name": "Alice", "role": "developer", "experience_level": "senior", "skills": ["Python", "React", "AWS"]},
            {"name": "Bob", "role": "developer", "experience_level": "mid", "skills": ["Python", "Docker"]},
            {"name": "Charlie", "role": "designer", "experience_level": "senior", "skills": ["Figma", "UI/UX"]},
        ]
    }

@pytest.fixture
def sample_codebase():
    """Create a temporary sample codebase for testing"""
    import tempfile
    import os
    
    tmp_dir = tempfile.mkdtemp()
    
    # Create sample Python files
    files = {
        "main.py": """
import os
import sys

def main():
    print("Hello, World!")
    
    # TODO: Add proper error handling
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
    verified: bool = False
""",
        "README.md": "# Test Project\n\nA sample project for testing.",
        "requirements.txt": "fastapi>=0.109.0\npytest>=7.4.0",
    }
    
    for filename, content in files.items():
        filepath = os.path.join(tmp_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
    
    yield tmp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
