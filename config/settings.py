from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    project_name: str = "PROJECT WARROOM"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://warroom:warroom_secret_2024@localhost:5432/warroom"
    redis_url: str = "redis://localhost:6379/0"
    chroma_db_url: str = "http://localhost:8000"
    chroma_db_path: str = "./data/chroma_db"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:latest"
    ollama_timeout: int = 60
    ollama_max_tokens: int = 2048
    ollama_temperature: float = 0.7

    embedding_model: str = "all-MiniLM-L6-v2"

    supported_code_extensions: str = ".py,.js,.ts,.java,.cpp,.go,.rs,.rb,.php"
    supported_doc_extensions: str = ".md,.txt,.pdf,.pptx,.docx"

    hackathon_readiness_threshold: float = 75.0
    architecture_risk_threshold: float = 25.0
    innovation_score_threshold: float = 80.0
    technical_debt_threshold: float = 30.0
    team_readiness_threshold: float = 65.0

    output_dir: str = "./output"
    report_format: str = "pdf"
    max_concurrent_projects: int = 10
    analysis_timeout_seconds: int = 300

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_code_extensions(self) -> List[str]:
        return self.supported_code_extensions.split(",")

    def get_doc_extensions(self) -> List[str]:
        return self.supported_doc_extensions.split(",")


settings = Settings()
