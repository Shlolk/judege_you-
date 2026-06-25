import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Container:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialize()

    def _initialize(self):
        from config.settings import settings
        self._services["settings"] = settings

        from ai.models.ollama_client import OllamaClient
        self._services["ollama_client"] = OllamaClient(
            base_url=settings.ollama_base_url, model=settings.ollama_model)

        from ai.embeddings import EmbeddingService
        self._services["embedding_service"] = EmbeddingService(model_name=settings.embedding_model)

        from parsers.code_parser import CodeParser
        self._services["code_parser"] = CodeParser()
        from parsers.document_parser import DocumentParser
        self._services["document_parser"] = DocumentParser()
        from parsers.ppt_parser import PPTParser
        self._services["ppt_parser"] = PPTParser()

        from database.repositories.project_repository import ProjectRepository
        self._services["project_repository"] = ProjectRepository()
        from database.repositories.analysis_repository import AnalysisRepository
        self._services["analysis_repository"] = AnalysisRepository()
        from database.repositories.team_repository import TeamRepository
        self._services["team_repository"] = TeamRepository()

        from core.services.analysis_service import AnalysisService
        self._services["analysis_service"] = AnalysisService(
            project_repository=self.get("project_repository"),
            analysis_repository=self.get("analysis_repository"),
            ollama_client=self.get("ollama_client"),
            embedding_service=self.get("embedding_service"),
            code_parser=self.get("code_parser"),
            document_parser=self.get("document_parser"),
            ppt_parser=self.get("ppt_parser"))

        from core.services.project_service import ProjectService
        self._services["project_service"] = ProjectService(
            project_repository=self.get("project_repository"),
            analysis_repository=self.get("analysis_repository"),
            team_repository=self.get("team_repository"),
            analyzer_service=self.get("analysis_service"))

        from modules.judge_simulation_engine import JudgeSimulationEngine
        self._services["judge_simulation"] = JudgeSimulationEngine(
            ollama_client=self.get("ollama_client"))
        from modules.interview_simulation_engine import InterviewSimulationEngine
        self._services["interview_simulation"] = InterviewSimulationEngine(
            ollama_client=self.get("ollama_client"))
        from modules.hackathon_readiness_engine import HackathonReadinessEngine
        self._services["hackathon_readiness"] = HackathonReadinessEngine(
            ollama_client=self.get("ollama_client"))
        from modules.weakness_detection_engine import WeaknessDetectionEngine
        self._services["weakness_detection"] = WeaknessDetectionEngine(
            ollama_client=self.get("ollama_client"),
            code_parser=self.get("code_parser"),
            document_parser=self.get("document_parser"))
        from modules.competitor_analysis_engine import CompetitorAnalysisEngine
        self._services["competitor_analysis"] = CompetitorAnalysisEngine(
            ollama_client=self.get("ollama_client"))
        from modules.ai_reasoning_engine import AIReasoningEngine
        self._services["ai_reasoning"] = AIReasoningEngine(
            ollama_client=self.get("ollama_client"))
        from modules.report_generator import ReportGenerator
        self._services["report_generator"] = ReportGenerator()
        from modules.knowledge_base_engine import KnowledgeBaseEngine
        self._services["knowledge_base"] = KnowledgeBaseEngine(
            ollama_client=self.get("ollama_client"),
            embedding_service=self.get("embedding_service"))
        from modules.project_scanner import ProjectScanner
        self._services["project_scanner"] = ProjectScanner()

        logger.info(f"Container initialized with {len(self._services)} services")

    def get(self, key: str) -> Any:
        return self._services.get(key)

    def register(self, key: str, service: Any):
        self._services[key] = service


container = Container()
