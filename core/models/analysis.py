from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

@dataclass
class AnalysisResult:
    id: str
    project_id: str
    analysis_type: str
    score: float
    details: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.details is None:
            self.details = {}
        if self.recommendations is None:
            self.recommendations = []

    @classmethod
    def from_project_analysis(cls, project_id: str, analysis_type: str,
                              analysis_result: Any) -> "AnalysisResult":
        return cls(id=str(uuid4()), project_id=project_id, analysis_type=analysis_type,
                   score=getattr(analysis_result, "overall_score", 0),
                   details=_extract_details(analysis_result),
                   recommendations=getattr(analysis_result, "recommendations", []),
                   created_at=datetime.now())

def _extract_details(result: Any) -> Dict[str, Any]:
    if hasattr(result, "__dataclass_fields__"):
        return {f: getattr(result, f) for f in result.__dataclass_fields__
                if not f.startswith("_") and not callable(getattr(result, f, None))}
    return {}
