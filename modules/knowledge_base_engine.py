import logging
logger = logging.getLogger(__name__)

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from core.models.project import Project
from ai.models.ollama_client import OllamaClient
from ai.embeddings import EmbeddingService

class EntryType(str, Enum):
    PATTERN = "pattern"
    BEST_PRACTICE = "best_practice"
    LESSON_LEARNED = "lesson_learned"
    COMMON_MISTAKE = "common_mistake"
    TIP = "tip"
    REFERENCE = "reference"
    CASE_STUDY = "case_study"

@dataclass
class KnowledgeEntry:
    id: str
    type: EntryType
    title: str
    content: str
    tags: List[str]
    source: str
    relevance_score: float
    usage_count: int
    created_at: datetime
    last_accessed: Optional[datetime] = None
    related_entries: List[str] = field(default_factory=list)

@dataclass
class QueryResult:
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    query_time_ms: float
    suggestions: List[str]

class KnowledgeBaseEngine:
    """Engine for managing and querying project knowledge base"""
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        embedding_service: EmbeddingService,
        kb_path: str = "./data/knowledge_base",
    ):
        self.ollama_client = ollama_client
        self.embedding_service = embedding_service
        self.kb_path = Path(kb_path)
        self.kb_path.mkdir(parents=True, exist_ok=True)
        self.entries: Dict[str, KnowledgeEntry] = {}
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load knowledge base from disk"""
        
        kb_file = self.kb_path / "knowledge_base.json"
        if kb_file.exists():
            try:
                with open(kb_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for entry_data in data:
                        if isinstance(entry_data.get("created_at"), str):
                            entry_data["created_at"] = datetime.fromisoformat(entry_data["created_at"])
                        if isinstance(entry_data.get("last_accessed"), str):
                            entry_data["last_accessed"] = datetime.fromisoformat(entry_data["last_accessed"])
                        entry = KnowledgeEntry(**entry_data)
                        self.entries[entry.id] = entry
            except:
                pass
        
        # Initialize with default entries if empty
        if not self.entries:
            self._initialize_default_entries()
    
    def _initialize_default_entries(self):
        """Initialize knowledge base with default entries"""
        
        defaults = [
            {
                "type": EntryType.BEST_PRACTICE,
                "title": "Clean Architecture Principles",
                "content": "Clean Architecture separates concerns into layers: entities, use cases, interface adapters, and frameworks. Each layer depends only on inner layers following the Dependency Inversion Principle.",
                "tags": ["architecture", "design-patterns", "clean-code"],
                "source": "Built-in knowledge base",
            },
            {
                "type": EntryType.BEST_PRACTICE,
                "title": "SOLID Principles",
                "content": "SOLID: Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. These principles ensure maintainable and scalable object-oriented design.",
                "tags": ["architecture", "design-patterns", "oop"],
                "source": "Built-in knowledge base",
            },
            {
                "type": EntryType.COMMON_MISTAKE,
                "title": "ChatGPT Wrapper Pitfall",
                "content": "Building a simple wrapper around ChatGPT/LLM APIs without unique data or algorithms creates no defensible moat. Add proprietary data, domain-specific logic, or novel UX to differentiate.",
                "tags": ["startup", "innovation", "llm", "ai"],
                "source": "Built-in knowledge base",
            },
            {
                "type": EntryType.TIP,
                "title": "Hackathon Presentation Tips",
                "content": "Focus on: (1) Problem statement in first 30 seconds, (2) Live demo over slides, (3) Architecture diagram for technical depth, (4) Business model briefly, (5) Q&A preparation for weak points.",
                "tags": ["hackathon", "presentation", "tips"],
                "source": "Built-in knowledge base",
            },
            {
                "type": EntryType.PATTERN,
                "title": "Microservices Communication Patterns",
                "content": "Common patterns: Event-Driven with message queues, API Gateway for routing, Circuit Breaker for fault tolerance, Saga for distributed transactions, CQRS for read/write separation.",
                "tags": ["architecture", "microservices", "patterns"],
                "source": "Built-in knowledge base",
            },
            {
                "type": EntryType.CASE_STUDY,
                "title": "Startup Failure: Feature Creep",
                "content": "A common startup failure pattern is adding too many features before achieving product-market fit. Focus on a single core feature that solves a painful problem before expanding.",
                "tags": ["startup", "product", "failure"],
                "source": "Built-in knowledge base",
            },
            {
                "type": EntryType.LESSON_LEARNED,
                "title": "Technical Debt Management",
                "content": "Technical debt should be tracked and allocated sprint capacity (20% rule). Refactor high-risk areas first, document all workarounds, and create automated tests before refactoring.",
                "tags": ["technical-debt", "engineering", "process"],
                "source": "Built-in knowledge base",
            },
            {
                "type": EntryType.BEST_PRACTICE,
                "title": "API Security Best Practices",
                "content": "Use HTTPS everywhere, implement rate limiting, validate all inputs, use JWT with short expiration, implement proper CORS, never expose internal errors, use API keys for machine-to-machine.",
                "tags": ["security", "api", "best-practices"],
                "source": "Built-in knowledge base",
            },
        ]
        
        for entry_data in defaults:
            entry = KnowledgeEntry(
                id=KnowledgeEntry.__name__ + datetime.now().strftime("%f"),
                type=entry_data["type"],
                title=entry_data["title"],
                content=entry_data["content"],
                tags=entry_data["tags"],
                source=entry_data["source"],
                relevance_score=0.8,
                usage_count=0,
                created_at=datetime.now(),
            )
            self.entries[entry.id] = entry
        
        self._save_knowledge_base()
    
    def _save_knowledge_base(self):
        """Save knowledge base to disk"""
        
        kb_file = self.kb_path / "knowledge_base.json"
        data = []
        for entry in self.entries.values():
            entry_dict = {
                "id": entry.id,
                "type": entry.type.value,
                "title": entry.title,
                "content": entry.content,
                "tags": entry.tags,
                "source": entry.source,
                "relevance_score": entry.relevance_score,
                "usage_count": entry.usage_count,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
                "related_entries": entry.related_entries,
            }
            data.append(entry_dict)
        
        with open(kb_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    async def query(
        self,
        query_text: str,
        max_results: int = 10,
        min_relevance: float = 0.3,
        filter_tags: Optional[List[str]] = None,
        filter_types: Optional[List[EntryType]] = None,
    ) -> QueryResult:
        """Query the knowledge base"""
        
        start_time = datetime.now()
        
        # Score entries against query
        scored_entries = []
        
        for entry in self.entries.values():
            relevance = await self._calculate_relevance(query_text, entry)
            
            if relevance < min_relevance:
                continue
            
            # Apply filters
            if filter_tags and not any(tag in entry.tags for tag in filter_tags):
                continue
            
            if filter_types and entry.type not in filter_types:
                continue
            
            scored_entries.append({
                "entry": entry,
                "relevance": relevance,
            })
        
        # Sort by relevance
        scored_entries.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Prepare results
        results = []
        for item in scored_entries[:max_results]:
            entry = item["entry"]
            entry.usage_count += 1
            entry.last_accessed = datetime.now()
            
            results.append({
                "id": entry.id,
                "type": entry.type.value,
                "title": entry.title,
                "content": entry.content[:300] + "..." if len(entry.content) > 300 else entry.content,
                "tags": entry.tags,
                "source": entry.source,
                "relevance": item["relevance"],
            })
        
        # Generate suggestions
        suggestions = await self._generate_suggestions(query_text, results)
        
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Save updates to disk
        self._save_knowledge_base()
        
        return QueryResult(
            query=query_text,
            results=results,
            total_results=len(results),
            query_time_ms=query_time,
            suggestions=suggestions,
        )
    
    async def _calculate_relevance(
        self,
        query: str,
        entry: KnowledgeEntry,
    ) -> float:
        """Calculate relevance of entry to query"""
        
        query_lower = query.lower()
        score = 0.0
        
        # Exact title match
        if entry.title.lower() == query_lower:
            score = 0.95
        elif entry.title.lower().startswith(query_lower):
            score = 0.85
        
        # Title contains query
        elif query_lower in entry.title.lower():
            score = 0.75
        
        # Content contains query
        elif query_lower in entry.content.lower():
            score = 0.55
        
        # Tag match
        elif any(tag.lower() in query_lower for tag in entry.tags):
            score = 0.40
        
        # Partial word matches in title
        else:
            query_words = set(query_lower.split())
            title_words = set(entry.title.lower().split())
            common_words = query_words & title_words
            if common_words:
                score = 0.25 * (len(common_words) / max(1, len(query_words)))
        
        # Combine with base relevance
        final_score = score * 0.7 + entry.relevance_score * 0.3
        
        return min(1.0, final_score)
    
    async def _generate_suggestions(
        self,
        query: str,
        results: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate follow-up suggestions based on query and results"""
        
        suggestions = []
        
        # Suggest related topics based on tags
        all_tags = set()
        for result in results:
            all_tags.update(result.get("tags", []))
        
        top_tags = list(all_tags)[:3]
        suggestions = [
            f"Explore entries tagged with '{tag}'" for tag in top_tags
        ]
        
        # Add default suggestions
        if not suggestions:
            suggestions = [
                "Try searching for 'architecture patterns'",
                "Search for 'hackathon tips'",
                "Explore 'security best practices'"
            ]
        
        return suggestions[:5]
    
    async def add_entry(
        self,
        entry_type: EntryType,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        source: str = "User",
        related_entries: Optional[List[str]] = None,
    ) -> KnowledgeEntry:
        """Add a new entry to the knowledge base"""
        
        entry = KnowledgeEntry(
            id=f"kb_{len(self.entries)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=entry_type,
            title=title,
            content=content,
            tags=tags or [],
            source=source,
            relevance_score=0.5,  # Start at neutral
            usage_count=0,
            created_at=datetime.now(),
            related_entries=related_entries or [],
        )
        
        self.entries[entry.id] = entry
        self._save_knowledge_base()
        
        return entry
    
    async def learn_from_project(
        self,
        project: Project,
        analysis_data: Dict[str, Any],
    ) -> List[KnowledgeEntry]:
        """Automatically extract knowledge from project analysis"""
        
        new_entries = []
        
        # Extract patterns from architecture
        if analysis_data.get("architectural_patterns"):
            content = f"Project '{project.name}' uses: {', '.join(analysis_data['architectural_patterns'][:3])}"
            entry = await self.add_entry(
                entry_type=EntryType.PATTERN,
                title=f"Architecture Pattern: {project.name}",
                content=content,
                tags=["architecture", "pattern", "auto-generated"],
                source=f"Project: {project.name}",
            )
            new_entries.append(entry)
        
        # Extract lessons from weaknesses
        weak_spots = analysis_data.get("weak_spots", [])
        if weak_spots:
            for spot in weak_spots[:2]:
                title = spot if isinstance(spot, str) else spot.get("title", "Lesson")
                entry = await self.add_entry(
                    entry_type=EntryType.LESSON_LEARNED,
                    title=f"Lesson: {title}",
                    content=f"From {project.name}: {spot}",
                    tags=["lesson", "auto-generated", "weakness"],
                    source=f"Project: {project.name}",
                )
                new_entries.append(entry)
        
        return new_entries
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        
        type_counts = {}
        for entry in self.entries.values():
            type_counts[entry.type.value] = type_counts.get(entry.type.value, 0) + 1
        
        total_usage = sum(e.usage_count for e in self.entries.values())
        
        top_entries = sorted(
            self.entries.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )[:5]
        
        return {
            "total_entries": len(self.entries),
            "entries_by_type": type_counts,
            "total_usage_count": total_usage,
            "average_relevance": sum(e.relevance_score for e in self.entries.values()) / max(1, len(self.entries)),
            "most_accessed": [
                {"title": e.title, "usage": e.usage_count}
                for e in top_entries
            ],
            "last_updated": max(
                (e.last_accessed or e.created_at for e in self.entries.values()),
                default=datetime.now()
            ).isoformat(),
        }

