import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Container:
    """Lazy-loading dependency injection container"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return
        self._initialized = True
        s = self._services

        from config.settings import settings
        s["settings"] = settings

        from ai.models.ollama_client import OllamaClient
        s["ollama_client"] = OllamaClient(
            base_url=settings.ollama_base_url, model=settings.ollama_model)

        from ai.embeddings import EmbeddingService
        s["embedding_service"] = EmbeddingService(model_name=settings.embedding_model)

        from parsers.code_parser import CodeParser
        s["code_parser"] = CodeParser()
        from parsers.document_parser import DocumentParser
        s["document_parser"] = DocumentParser()
        from parsers.ppt_parser import PPTParser
        s["ppt_parser"] = PPTParser()

        from database.repositories.project_repository import ProjectRepository
        s["project_repository"] = ProjectRepository()
        from database.repositories.analysis_repository import AnalysisRepository
        s["analysis_repository"] = AnalysisRepository()
        from database.repositories.team_repository import TeamRepository
        s["team_repository"] = TeamRepository()

        from modules.judge_simulation_engine import JudgeSimulationEngine
        s["judge_simulation"] = JudgeSimulationEngine(ollama_client=s["ollama_client"])
        from modules.interview_simulation_engine import InterviewSimulationEngine
        s["interview_simulation"] = InterviewSimulationEngine(ollama_client=s["ollama_client"])
        from modules.hackathon_readiness_engine import HackathonReadinessEngine
        s["hackathon_readiness"] = HackathonReadinessEngine(ollama_client=s["ollama_client"])
        from modules.weakness_detection_engine import WeaknessDetectionEngine
        s["weakness_detection"] = WeaknessDetectionEngine(
            ollama_client=s["ollama_client"], code_parser=s["code_parser"],
            document_parser=s["document_parser"])
        from modules.competitor_analysis_engine import CompetitorAnalysisEngine
        s["competitor_analysis"] = CompetitorAnalysisEngine(ollama_client=s["ollama_client"])
        from modules.ai_reasoning_engine import AIReasoningEngine
        s["ai_reasoning"] = AIReasoningEngine(ollama_client=s["ollama_client"])
        from modules.architecture_auditor import ArchitectureAuditor
        s["architecture_auditor"] = ArchitectureAuditor(ollama_client=s["ollama_client"])
        from modules.report_generator import ReportGenerator
        s["report_generator"] = ReportGenerator()
        from modules.knowledge_base_engine import KnowledgeBaseEngine
        s["knowledge_base"] = KnowledgeBaseEngine(
            ollama_client=s["ollama_client"], embedding_service=s["embedding_service"])
        from modules.project_scanner import ProjectScanner
        s["project_scanner"] = ProjectScanner()

        from modules.roast_engine import RoastEngine
        s["roast_engine"] = RoastEngine(ollama_client=s["ollama_client"])

        from core.services.analysis_service import AnalysisService
        s["analysis_service"] = AnalysisService(
            project_repository=s["project_repository"],
            analysis_repository=s["analysis_repository"],
            ollama_client=s["ollama_client"],
            embedding_service=s["embedding_service"],
            code_parser=s["code_parser"],
            document_parser=s["document_parser"],
            ppt_parser=s["ppt_parser"],
            architecture_auditor=s["architecture_auditor"],
            hackathon_engine=s["hackathon_readiness"],
            weakness_engine=s["weakness_detection"],
            competitor_engine=s["competitor_analysis"])

        from core.services.project_service import ProjectService
        s["project_service"] = ProjectService(
            project_repository=s["project_repository"],
            analysis_repository=s["analysis_repository"],
            team_repository=s["team_repository"],
            analyzer_service=s["analysis_service"])

        logger.info(f"Container initialized with {len(s)} services")

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        if not self._initialized:
            self._initialize()
        return self._services.get(key, default)

    def register(self, key: str, service: Any):
        self._services[key] = service


_container_instance: Optional[Container] = None


def get_container() -> Container:
    global _container_instance
    if _container_instance is None:
        _container_instance = Container()
    return _container_instance


container = get_container()
