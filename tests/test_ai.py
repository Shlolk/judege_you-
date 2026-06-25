"""Tests for AI layer (Ollama client, embeddings)"""

import pytest


class TestOllamaClient:
    """Test the Ollama client"""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test client initialization"""
        from ai.models.ollama_client import OllamaClient

        client = OllamaClient(base_url="http://localhost:11434", model="gemma3:latest")
        assert client.base_url == "http://localhost:11434"
        assert client.model == "gemma3:latest"
        assert client.client is None

    @pytest.mark.asyncio
    async def test_generate_fallback_to_mock(self):
        """Test generate falls back to mock response when Ollama unreachable"""
        from ai.models.ollama_client import OllamaClient

        client = OllamaClient(base_url="http://localhost:99999", model="gemma3:latest")
        response = await client.generate("Analyze architecture of test project")
        assert response is not None
        assert len(response) > 0
        # Should include mock score
        assert "Score" in response or "score" in response.lower()

    @pytest.mark.asyncio
    async def test_structured_fallback(self):
        """Test structured response falls back to mock"""
        from ai.models.ollama_client import OllamaClient

        client = OllamaClient(base_url="http://localhost:99999", model="gemma3:latest")
        result = await client.generate_structured(
            "Analyze architecture of test project",
            schema={"type": "object", "properties": {"score": {"type": "number"}}},
        )
        assert isinstance(result, dict)
        assert "score" in result

    @pytest.mark.asyncio
    async def test_context_aware_mock(self):
        """Test mock responses are context-aware"""
        from ai.models.ollama_client import OllamaClient

        client = OllamaClient(base_url="http://localhost:99999", model="gemma3:latest")

        arch = await client.generate("Analyze the architecture of my project")
        hack = await client.generate("Evaluate hackathon readiness")
        tech = await client.generate("How much technical debt?")

        # Different topics should produce different responses
        assert arch != hack or arch != tech  # At least one differs

    @pytest.mark.asyncio
    async def test_close(self):
        """Test client close doesn't crash"""
        from ai.models.ollama_client import OllamaClient

        client = OllamaClient()
        await client.close()
        assert client.client is None


class TestEmbeddingService:
    """Test the embedding service"""

    @pytest.mark.asyncio
    async def test_embed_text(self):
        """Test text embedding generation"""
        from ai.embeddings import EmbeddingService

        service = EmbeddingService()
        # This might fail if sentence-transformers not installed
        try:
            embedding = await service.embed_text("Hello world")
            assert isinstance(embedding, list)
            assert len(embedding) > 0
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    @pytest.mark.asyncio
    async def test_compute_similarity(self):
        """Test similarity computation"""
        from ai.embeddings import EmbeddingService

        service = EmbeddingService()
        try:
            similarity = await service.compute_similarity("Hello", "World")
            assert isinstance(similarity, float)
            assert -1 <= similarity <= 1
        except ImportError:
            pytest.skip("sentence-transformers not installed")
