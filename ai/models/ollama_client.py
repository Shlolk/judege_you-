"""Ollama client for Gemma 3 AI inference"""

import logging
import json
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama (Gemma 3) for AI analysis.

    Connects to a running Ollama instance. Falls back to mock responses
    when Ollama is unreachable (development/demo mode).
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma3:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = None

    async def _ensure_client(self):
        if self.client is not None:
            return True
        try:
            import httpx
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
            # Verify connection
            resp = await self.client.get("/api/tags", timeout=5.0)
            resp.raise_for_status()
            available_models = [m["name"] for m in resp.json().get("models", [])]
            if self.model not in available_models:
                logger.warning(f"Model '{self.model}' not found in Ollama. Available: {available_models[:5]}")
            logger.info(f"Connected to Ollama at {self.base_url}")
            return True
        except ImportError:
            logger.warning("httpx not installed. Install with: pip install httpx")
        except Exception as e:
            logger.warning(f"Ollama not reachable at {self.base_url}: {e}")
            self.client = None
        return False

    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text from the model. Falls back to mock on failure."""
        connected = await self._ensure_client()
        if connected and self.client:
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                }
                if system_prompt:
                    payload["system"] = system_prompt
                response = await self.client.post("/api/generate", json=payload)
                response.raise_for_status()
                return response.json()["response"]
            except Exception as e:
                logger.debug(f"Ollama generate failed: {e}")
        return self._mock_response(prompt)

    async def generate_structured(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate structured JSON from the model."""
        text = await self.generate(
            prompt,
            system_prompt="Respond with valid JSON only. No markdown, no explanation. Return a JSON object.",
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return self._mock_structured(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Generate context-aware mock response when Ollama is unavailable."""
        p = prompt.lower()

        if "architecture" in p:
            score = 78
            return (f"Score: {score}\nThe architecture shows good separation of concerns. "
                    f"Consider improving error handling and adding monitoring. "
                    f"Recommendations: Add caching layer, implement health checks, use message queues.")
        if "hackathon" in p:
            score = 72
            return (f"Score: {score}\nProject has solid MVP potential. "
                    f"Need better time management and documentation. "
                    f"Recommendations: Create demo script, prepare pitch deck, practice Q&A.")
        if "innovation" in p or "novel" in p:
            score = 82
            return (f"Score: {score}\nHigh innovation potential. Unique approach to problem solving. "
                    f"Market validation recommended.")
        if "technical debt" in p or "debt" in p:
            score = 25
            return (f"Score: {score}\nLow to moderate technical debt. "
                    f"Refactoring recommended for core modules. Test coverage needs improvement.")
        if "team" in p:
            score = 70
            return (f"Score: {score}\nGood technical skills across the team. "
                    f"Consider improving cross-functional coordination and adding senior mentorship.")
        if "competitive" in p or "competitor" in p or "market" in p:
            score = 68
            return (f"Score: {score}\nModerate competitive position. "
                    f"Unique features provide differentiation opportunity. "
                    f"Target niche market segments for initial traction.")
        if "weakness" in p or "vulnerability" in p:
            return ("Category:architecture|Severity:medium|Description:Tight coupling in data layer\n"
                    "Category:testing|Severity:high|Description:Insufficient test coverage\n"
                    "Category:documentation|Severity:medium|Description:Missing API documentation")
        if "question" in p or "interview" in p:
            return ("Category:technical|Difficulty:7|Explain your system architecture and key design decisions.\n"
                    "Category:behavioral|Difficulty:5|Describe a time you had to handle a technical disagreement.\n"
                    "Category:system_design|Difficulty:8|Design a system that handles 1M requests per day.")
        return "Score: 70\nAnalysis completed successfully. Project shows good potential."

    def _mock_structured(self, prompt: str) -> Dict[str, Any]:
        """Generate structured mock response."""
        p = prompt.lower()
        if "architecture" in p:
            return {
                "score": 78.0, "risk_level": "medium", "pattern": "Modular Monolith",
                "strengths": ["Clean separation of concerns", "Good documentation", "Well-structured codebase"],
                "weaknesses": ["Limited horizontal scalability", "No caching layer", "Tight coupling in modules"],
                "recommendations": ["Add caching layer", "Consider event-driven architecture", "Implement health checks"],
                "technical_debt": 25.0, "scalability_rating": 65.0,
                "maintainability_rating": 78.0, "innovation_rating": 60.0,
            }
        return {
            "score": 72.0, "risk_level": "medium",
            "strengths": ["Good foundation", "Clear design"],
            "weaknesses": ["Limited testing", "Documentation gaps"],
            "recommendations": ["Increase test coverage", "Add architecture docs"],
            "details": {"architecture": 78, "innovation": 72, "quality": 68},
        }

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None
