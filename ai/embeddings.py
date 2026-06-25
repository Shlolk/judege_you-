import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

    async def initialize(self):
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")

    async def embed_text(self, text: str) -> List[float]:
        await self.initialize()
        if self.model:
            return self.model.encode(text).tolist()
        return [0.0] * 384

    async def embed_documents(self, documents: List[str], batch_size: int = 32) -> List[List[float]]:
        await self.initialize()
        if self.model:
            return self.model.encode(documents, batch_size=batch_size).tolist()
        return [[0.0] * 384 for _ in documents]

    async def compute_similarity(self, text1: str, text2: str) -> float:
        await self.initialize()
        if self.model:
            emb1 = self.model.encode([text1])[0]
            emb2 = self.model.encode([text2])[0]
            return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        return 0.5

    async def find_most_similar(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        await self.initialize()
        if not self.model:
            return [{"document": d, "similarity": 0.5, "index": i} for i, d in enumerate(documents[:top_k])]
        query_emb = self.model.encode([query])[0]
        doc_embs = self.model.encode(documents)
        similarities = [float(np.dot(query_emb, de) / (np.linalg.norm(query_emb) * np.linalg.norm(de)))
                        for de in doc_embs]
        indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:top_k]
        return [{"document": documents[i], "similarity": similarities[i], "index": i} for i in indices]
