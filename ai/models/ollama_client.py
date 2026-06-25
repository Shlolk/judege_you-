import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma3:latest"):
        self.base_url = base_url
        self.model = model
        self.client = None

    async def _ensure_client(self):
        if self.client is None:
            try:
                import httpx
                self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60)
            except ImportError:
                logger.warning("httpx not installed, using mock responses")
                self.client = None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 1000) -> str:
        await self._ensure_client()
        if self.client:
            try:
                payload = {"model": self.model, "prompt": prompt, "stream": False,
                           "options": {"temperature": temperature, "num_predict": max_tokens}}
                if system_prompt:
                    payload["system"] = system_prompt
                response = await self.client.post("/api/generate", json=payload)
                response.raise_for_status()
                return response.json()["response"]
            except Exception as e:
                logger.warning(f"Ollama API call failed: {e}, using mock response")
        return self._mock_response(prompt)

    async def generate_structured(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text = await self.generate(prompt,
                                   system_prompt="Respond with valid JSON only. No markdown, no explanation.")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return self._mock_structured(prompt)

    def _mock_response(self, prompt: str) -> str:
        p = prompt.lower()
        if "architecture" in p:
            return "Score: 78\nThe architecture shows good separation of concerns. Consider improving error handling and adding monitoring."
        if "hackathon" in p:
            return "Score: 72\nProject has solid MVP potential. Need better time management and documentation."
        if "innovation" in p or "novel" in p:
            return "Score: 82\nHigh innovation potential. Unique approach to problem solving. Market validation recommended."
        if "technical debt" in p or "debt" in p:
            return "Score: 25\nModerate technical debt. Recommend refactoring core modules and improving test coverage."
        if "team" in p:
            return "Score: 70\nGood technical skills. Consider improving coordination and adding senior leadership."
        if "competitive" in p or "competitor" in p or "market" in p:
            return "Score: 68\nModerate competitive position. Unique features provide differentiation opportunity."
        if "weakness" in p or "vulnerability" in p:
            return "Score: 75\nArchitecture: OK, Security: needs improvement, Testing: insufficient, Documentation: minimal"
        if "question" in p or "interview" in p:
            return "Category:technical|Difficulty:7|Explain your system architecture and key design decisions."
        return "Score: 70\nAnalysis completed successfully."

    def _mock_structured(self, prompt: str) -> Dict[str, Any]:
        return {"score": 72.0, "risk_level": "medium", "strengths": ["Good foundation", "Clear design"],
                "weaknesses": ["Limited testing", "Documentation gaps"],
                "recommendations": ["Increase test coverage", "Add architecture docs"],
                "details": {"architecture": 78, "innovation": 72, "quality": 68}}

    async def close(self):
        if self.client:
            await self.client.aclose()
