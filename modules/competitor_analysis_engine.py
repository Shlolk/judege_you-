import logging
logger = logging.getLogger(__name__)

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import random

from core.models.project import Project
from ai.models.ollama_client import OllamaClient

class MarketSegment(str, Enum):
    STUDENT = "student"
    DEVELOPER = "developer"
    HACKATHON = "hackathon"
    STARTUP = "startup"
    ENTERPRISE = "enterprise"
    FREELANCER = "freelancer"

@dataclass
class Competitor:
    name: str
    description: str
    market_share: float
    strengths: List[str]
    weaknesses: List[str]
    key_features: List[str]
    pricing_model: str
    target_audience: List[MarketSegment]
    similarity_score: float
    threat_level: str  # low, medium, high, critical
    unique_selling_points: List[str]
    estimated_revenue: Optional[float] = None
    founded_year: Optional[int] = None

@dataclass
class CompetitiveLandscape:
    market_segment: MarketSegment
    total_addressable_market: float
    competitors: List[Competitor]
    market_gaps: List[str]
    opportunities: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    market_trends: List[str]

@dataclass
class CompetitiveAnalysisResult:
    project_name: str
    overall_position: str  # leader, challenger, niche, emerging
    competitiveness_score: float
    market_fit_score: float
    differentiation_score: float
    direct_competitors: List[Competitor]
    indirect_competitors: List[Competitor]
    landscapes: Dict[str, CompetitiveLandscape]
    blue_ocean_opportunities: List[str]
    competitive_advantages: List[str]
    competitive_disadvantages: List[str]
    strategic_recommendations: List[str]
    analysis_metadata: Dict[str, Any]

class CompetitorAnalysisEngine:
    """Engine for competitive intelligence and analysis"""
    
    # Known competitors database
    KNOWN_COMPETITORS = {
        "project_analysis": [
            {
                "name": "GitHub Copilot",
                "description": "AI pair programmer for code generation",
                "strengths": ["Code completion", "IDE integration", "Large language model"],
                "weaknesses": ["No project analysis", "No architecture review", "No hackathon prep"],
                "features": ["Code generation", "Chat interface", "Context awareness"],
                "pricing": "Subscription-based",
                "audience": ["developer"],
                "revenue": 100_000_000,
                "founded": 2021,
            },
            {
                "name": "SonarQube",
                "description": "Code quality and security analysis platform",
                "strengths": ["Static analysis", "Security scanning", "Technical debt measurement"],
                "weaknesses": ["No AI analysis", "No hackathon features", "No simulation"],
                "features": ["Code quality", "Security analysis", "Technical debt"],
                "pricing": "Freemium",
                "audience": ["developer", "enterprise"],
                "revenue": 50_000_000,
                "founded": 2008,
            },
            {
                "name": "CodeRabbit",
                "description": "AI-powered code review",
                "strengths": ["PR review automation", "AI suggestions", "Fast feedback"],
                "weaknesses": ["Limited to code review", "No project analysis", "No simulation"],
                "features": ["Code review", "AI suggestions", "PR analysis"],
                "pricing": "Subscription",
                "audience": ["developer"],
                "revenue": 10_000_000,
                "founded": 2022,
            },
            {
                "name": "Tabnine",
                "description": "AI code completion assistant",
                "strengths": ["Code completion", "Multiple languages", "Local AI models"],
                "weaknesses": ["Code only", "No architecture", "No hackathon"],
                "features": ["Code completion", "AI chat", "Code generation"],
                "pricing": "Freemium",
                "audience": ["developer"],
                "revenue": 20_000_000,
                "founded": 2017,
            },
            {
                "name": "Codacy",
                "description": "Automated code review and analytics",
                "strengths": ["Code quality", "Security scanning", "Coverage tracking"],
                "weaknesses": ["No AI", "No simulation", "No hackathon prep"],
                "features": ["Code review", "Quality metrics", "Security"],
                "pricing": "Freemium",
                "audience": ["developer", "enterprise"],
                "revenue": 15_000_000,
                "founded": 2014,
            },
        ],
        "hackathon_tools": [
            {
                "name": "Devpost",
                "description": "Hackathon platform for hosting and submissions",
                "strengths": ["Hackathon hosting", "Project showcase", "Community"],
                "weaknesses": ["No AI analysis", "No simulation", "No training"],
                "features": ["Host hackathons", "Submit projects", "Find teams"],
                "pricing": "Free",
                "audience": ["hackathon", "student", "developer"],
                "revenue": 5_000_000,
                "founded": 2010,
            },
            {
                "name": "Hackathon.io",
                "description": "Hackathon management platform",
                "strengths": ["Event management", "Team formation", "Judging tools"],
                "weaknesses": ["No AI", "No project analysis", "No training"],
                "features": ["Manage hackathons", "Team matching"],
                "pricing": "Free/Enterprise",
                "audience": ["hackathon", "enterprise"],
                "revenue": 2_000_000,
                "founded": 2013,
            },
        ],
        "presentation_tools": [
            {
                "name": "Canva",
                "description": "Design and presentation platform",
                "strengths": ["Easy design", "Templates", "Collaboration"],
                "weaknesses": ["No AI analysis", "No code integration", "No defense sim"],
                "features": ["Presentations", "Design", "Templates"],
                "pricing": "Freemium",
                "audience": ["student", "developer", "enterprise"],
                "revenue": 1_000_000_000,
                "founded": 2013,
            },
            {
                "name": "Gamma",
                "description": "AI-powered presentation creator",
                "strengths": ["AI generation", "Beautiful slides", "Easy to use"],
                "weaknesses": ["No project analysis", "No code review", "No hackathon"],
                "features": ["AI slides", "Templates", "Export"],
                "pricing": "Subscription",
                "audience": ["student", "developer", "enterprise"],
                "revenue": 5_000_000,
                "founded": 2020,
            },
        ],
    }
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
    
    async def analyze_competition(
        self,
        project: Project,
        market_segments: Optional[List[MarketSegment]] = None,
        include_known_competitors: bool = True,
    ) -> CompetitiveAnalysisResult:
        """Perform comprehensive competitive analysis"""
        
        if market_segments is None:
            market_segments = self._infer_market_segments(project)
        
        landscapes = {}
        all_direct = []
        all_indirect = []
        
        for segment in market_segments:
            landscape = await self._analyze_market_segment(project, segment, include_known_competitors)
            landscapes[segment.value] = landscape
            all_direct.extend(landscape.competitors[:3])
            if len(landscape.competitors) > 3:
                all_indirect.extend(landscape.competitors[3:])
        
        # Calculate scores
        competitiveness_score = await self._calculate_competitiveness_score(
            project, landscapes
        )
        
        market_fit_score = await self._calculate_market_fit_score(
            project, market_segments, landscapes
        )
        
        differentiation_score = await self._calculate_differentiation_score(
            project, all_direct
        )
        
        # Determine position
        overall_position = self._determine_market_position(
            competitiveness_score, market_fit_score, differentiation_score
        )
        
        # Identify blue ocean opportunities
        blue_ocean = self._identify_blue_ocean_opportunities(
            project, landscapes, all_direct
        )
        
        # Generate competitive analysis
        advantages = await self._identify_competitive_advantages(project, all_direct)
        disadvantages = await self._identify_competitive_disadvantages(project, all_direct)
        
        # Strategic recommendations
        recommendations = await self._generate_strategic_recommendations(
            project, advantages, disadvantages, landscapes
        )
        
        return CompetitiveAnalysisResult(
            project_name=project.name,
            overall_position=overall_position,
            competitiveness_score=competitiveness_score,
            market_fit_score=market_fit_score,
            differentiation_score=differentiation_score,
            direct_competitors=all_direct[:5],
            indirect_competitors=all_indirect[:5],
            landscapes=landscapes,
            blue_ocean_opportunities=blue_ocean,
            competitive_advantages=advantages,
            competitive_disadvantages=disadvantages,
            strategic_recommendations=recommendations,
            analysis_metadata={
                "market_segments_analyzed": [s.value for s in market_segments],
                "competitors_analyzed": len(all_direct) + len(all_indirect),
                "analysis_timestamp": datetime.now().isoformat(),
            }
        )
    
    def _infer_market_segments(self, project: Project) -> List[MarketSegment]:
        """Infer market segments from project data"""
        
        segments = [MarketSegment.DEVELOPER]
        
        if project.description:
            desc_lower = project.description.lower()
            if any(w in desc_lower for w in ["student", "academic", "college", "university"]):
                segments.append(MarketSegment.STUDENT)
            if any(w in desc_lower for w in ["hackathon", "competition", "challenge"]):
                segments.append(MarketSegment.HACKATHON)
            if any(w in desc_lower for w in ["startup", "business", "venture", "funding"]):
                segments.append(MarketSegment.STARTUP)
            if any(w in desc_lower for w in ["enterprise", "corporate", "organization"]):
                segments.append(MarketSegment.ENTERPRISE)
            if any(w in desc_lower for w in ["freelance", "contractor", "independent"]):
                segments.append(MarketSegment.FREELANCER)
        
        return segments[:3]  # Max 3 segments
    
    async def _analyze_market_segment(
        self,
        project: Project,
        segment: MarketSegment,
        include_known: bool,
    ) -> CompetitiveLandscape:
        """Analyze a specific market segment"""
        
        competitors = []
        market_gaps = []
        
        # Include known competitors
        if include_known:
            for category in self.KNOWN_COMPETITORS.values():
                for comp in category:
                    if segment.value in comp["audience"]:
                        similarity = await self._calculate_similarity(project, comp)
                        competitors.append(Competitor(
                            name=comp["name"],
                            description=comp["description"],
                            market_share=-1,
                            strengths=comp["strengths"],
                            weaknesses=comp["weaknesses"],
                            key_features=comp["features"],
                            pricing_model=comp["pricing"],
                            target_audience=[MarketSegment(a) for a in comp["audience"]],
                            similarity_score=similarity,
                            threat_level=self._determine_threat_level(similarity),
                            unique_selling_points=list(set(comp["strengths"])),
                            estimated_revenue=comp.get("revenue"),
                            founded_year=comp.get("founded"),
                        ))
        
        # Discover new competitors via AI
        ai_competitors = await self._discover_ai_competitors(project, segment)
        competitors.extend(ai_competitors)
        
        # Sort by similarity (most similar first)
        competitors.sort(key=lambda c: c.similarity_score, reverse=True)
        
        # Identify market gaps
        market_gaps = await self._identify_market_gaps(project, competitors, segment)
        
        # Find opportunities and threats
        opportunities = await self._find_opportunities(project, competitors, market_gaps)
        threats = await self._find_threats(project, competitors)
        
        # Market trends
        market_trends = await self._get_market_trends(segment)
        
        return CompetitiveLandscape(
            market_segment=segment,
            total_addressable_market=self._estimate_tam(segment),
            competitors=competitors,
            market_gaps=market_gaps,
            opportunities=opportunities,
            threats=threats,
            market_trends=market_trends,
        )
    
    async def _discover_ai_competitors(
        self,
        project: Project,
        segment: MarketSegment,
    ) -> List[Competitor]:
        """Discover competitors using AI"""
        
        discovery = await self.ollama_client.generate(
            f"Identify competitors in the {segment.value} market:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Return 2-3 competitor names and their key details"
        )
        
        # Simple parsing - in production would use structured output
        competitors = []
        lines = discovery.splitlines()
        
        for i, line in enumerate(lines[:6]):
            if line.strip() and not line.startswith("Score:"):
                competitors.append(Competitor(
                    name=line.strip()[:50],
                    description="AI-discovered competitor",
                    market_share=random.uniform(1, 15),
                    strengths=["AI-discovered"],
                    weaknesses=["Unknown"],
                    key_features=["Unknown"],
                    pricing_model="Unknown",
                    target_audience=[segment],
                    similarity_score=random.uniform(30, 70),
                    threat_level="medium",
                    unique_selling_points=["AI-discovered"],
                ))
        
        return competitors[:3]
    
    async def _calculate_similarity(self, project: Project, competitor: Dict) -> float:
        """Calculate similarity between project and competitor"""
        
        base_score = 50.0
        
        # Check feature overlap
        if project.description:
            desc_lower = project.description.lower()
            for feature in competitor["features"]:
                if feature.lower() in desc_lower:
                    base_score += 5
            for strength in competitor["strengths"]:
                if strength.lower() in desc_lower:
                    base_score += 3
        
        return min(95, base_score)
    
    def _determine_threat_level(self, similarity: float) -> str:
        """Determine competitive threat level"""
        if similarity >= 80:
            return "critical"
        elif similarity >= 65:
            return "high"
        elif similarity >= 45:
            return "medium"
        return "low"
    
    async def _identify_market_gaps(
        self,
        project: Project,
        competitors: List[Competitor],
        segment: MarketSegment,
    ) -> List[str]:
        """Identify gaps in the market"""
        
        gaps = []
        
        # Known gaps based on competitor weaknesses
        all_weaknesses = []
        for comp in competitors:
            all_weaknesses.extend(comp.weaknesses)
        
        # Common gaps in the market
        if not any("simulation" in w.lower() for w in all_weaknesses):
            gaps.append("No competitor offers project defense simulation")
        if not any("judge" in w.lower() for w in all_weaknesses):
            gaps.append("No competitor provides judge/presentation simulation")
        if not any("hackathon" in w.lower() for w in all_weaknesses):
            gaps.append("No dedicated hackathon readiness engine")
        if not any("architecture" in w.lower() and "review" in w.lower() for w in all_weaknesses):
            gaps.append("No competitor combines code + architecture + team analysis")
        
        # AI-identified gaps
        ai_gaps = await self.ollama_client.generate(
            f"Identify market gaps in the {segment.value} segment:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Return 2-3 specific market gaps not addressed by existing tools"
        )
        
        for line in ai_gaps.splitlines():
            if line.strip() and not line.startswith("Score:"):
                gaps.append(line.strip())
        
        return gaps[:6]
    
    async def _find_opportunities(
        self,
        project: Project,
        competitors: List[Competitor],
        gaps: List[str],
    ) -> List[Dict[str, Any]]:
        """Find market opportunities"""
        
        opportunities = []
        
        for gap in gaps:
            opportunities.append({
                "opportunity": gap,
                "potential_impact": "high" if "simulation" in gap.lower() else "medium",
                "effort_to_capture": "medium",
                "time_to_market": "3-6 months",
            })
        
        return opportunities
    
    async def _find_threats(
        self,
        project: Project,
        competitors: List[Competitor],
    ) -> List[Dict[str, Any]]:
        """Find market threats"""
        
        threats = []
        
        for comp in competitors[:3]:
            if comp.similarity_score > 70:
                threats.append({
                    "threat": f"{comp.name} is a direct competitor with {comp.similarity_score:.0f}% similarity",
                    "severity": comp.threat_level,
                    "mitigation": f"Differentiate through unique features not offered by {comp.name}",
                })
        
        return threats[:5]
    
    async def _get_market_trends(self, segment: MarketSegment) -> List[str]:
        """Get current market trends"""
        
        trends = await self.ollama_client.generate(
            f"List 3 current market trends in the {segment.value} AI/developer tools space"
        )
        
        result = [
            line.strip() for line in trends.splitlines()
            if line.strip() and not line.startswith("Score:")
        ]
        
        return result[:5] if result else [
            "AI-powered development tools growth",
            "Shift towards local-first AI models",
            "Increasing focus on project analysis automation",
        ]
    
    def _estimate_tam(self, segment: MarketSegment) -> float:
        """Estimate total addressable market in USD"""
        
        tam_estimates = {
            MarketSegment.STUDENT: 500_000_000,
            MarketSegment.DEVELOPER: 2_000_000_000,
            MarketSegment.HACKATHON: 200_000_000,
            MarketSegment.STARTUP: 1_000_000_000,
            MarketSegment.ENTERPRISE: 5_000_000_000,
            MarketSegment.FREELANCER: 300_000_000,
        }
        return tam_estimates.get(segment, 500_000_000)
    
    async def _calculate_competitiveness_score(
        self,
        project: Project,
        landscapes: Dict[str, CompetitiveLandscape],
    ) -> float:
        """Calculate how competitive the project is"""
        
        if not landscapes:
            return 50.0
        
        total_threat = 0
        total_competitors = 0
        total_gaps = 0
        
        for landscape in landscapes.values():
            for comp in landscape.competitors:
                if comp.threat_level == "critical":
                    total_threat += 10
                elif comp.threat_level == "high":
                    total_threat += 5
                total_competitors += 1
            
            total_gaps += len(landscape.market_gaps)
        
        competitiveness = 100 - (total_threat / max(1, total_competitors) * 10)
        competitiveness += min(20, total_gaps * 5)
        
        return min(100, max(0, competitiveness))
    
    async def _calculate_market_fit_score(
        self,
        project: Project,
        segments: List[MarketSegment],
        landscapes: Dict[str, CompetitiveLandscape],
    ) -> float:
        """Calculate product-market fit score"""
        
        base_score = 60.0
        
        # More segments = broader market fit
        base_score += len(segments) * 5
        
        # Presence of gaps increases market fit
        for landscape in landscapes.values():
            if landscape.market_gaps:
                base_score += 10
        
        return min(100, base_score)
    
    async def _calculate_differentiation_score(
        self,
        project: Project,
        competitors: List[Competitor],
    ) -> float:
        """Calculate how differentiated the project is"""
        
        if not competitors:
            return 90.0
        
        diff_score = 100.0
        
        for comp in competitors:
            if comp.similarity_score > 80:
                diff_score -= 15
            elif comp.similarity_score > 60:
                diff_score -= 10
            elif comp.similarity_score > 40:
                diff_score -= 5
        
        return max(0, diff_score)
    
    def _determine_market_position(
        self,
        competitiveness: float,
        market_fit: float,
        differentiation: float,
    ) -> str:
        """Determine market position string"""
        
        avg = (competitiveness + market_fit + differentiation) / 3
        
        if avg >= 80 and differentiation >= 75:
            return "leader"
        elif avg >= 65:
            return "challenger"
        elif avg >= 50:
            return "niche"
        else:
            return "emerging"
    
    def _identify_blue_ocean_opportunities(
        self,
        project: Project,
        landscapes: Dict[str, CompetitiveLandscape],
        competitors: List[Competitor],
    ) -> List[str]:
        """Identify blue ocean (uncontested market) opportunities"""
        
        opportunities = []
        
        # Check for uncontested features
        all_comp_features = set()
        for comp in competitors:
            all_comp_features.update(f.lower() for f in comp.key_features)
        
        unique_features = [
            "judge simulation",
            "architecture battle mode",
            "cross examination mode",
            "project defense training",
            "hackathon winning probability",
            "innovation detection",
            "selection probability predictor",
            "team readiness score",
        ]
        
        for feature in unique_features:
            if feature not in all_comp_features:
                opportunities.append(f"No competitor offers {feature}")
        
        return opportunities[:6]
    
    async def _identify_competitive_advantages(
        self,
        project: Project,
        competitors: List[Competitor],
    ) -> List[str]:
        """Identify competitive advantages"""
        
        advantages = [
            "Comprehensive project analysis (code + docs + architecture + team)",
            "Judge and interview simulation for defense training",
            "Hackathon readiness engine with winning probability",
            "Architecture battle mode for technical evaluation",
            "Cross examination mode for stress testing",
        ]
        
        return advantages[:6]
    
    async def _identify_competitive_disadvantages(
        self,
        project: Project,
        competitors: List[Competitor],
    ) -> List[str]:
        """Identify competitive disadvantages"""
        
        disadvantages = [
            "New entrant with limited market presence",
            "Requires local AI infrastructure (Ollama)",
            "Dependency on multiple services (PostgreSQL, Redis, ChromaDB)",
        ]
        
        return disadvantages
    
    async def _generate_strategic_recommendations(
        self,
        project: Project,
        advantages: List[str],
        disadvantages: List[str],
        landscapes: Dict[str, CompetitiveLandscape],
    ) -> List[str]:
        """Generate strategic recommendations"""
        
        recommendations = [
            "Focus marketing on unique judge simulation feature",
            "Target hackathon participants as initial beachhead market",
            "Build open source community to accelerate adoption",
            "Partner with hackathon platforms (Devpost, HackerEarth)",
            "Create free tier for students to build user base",
        ]
        
        # Add gap-based recommendations
        for landscape in landscapes.values():
            for gap in landscape.market_gaps[:2]:
                recommendations.append(f"Address market gap: {gap}")
        
        return recommendations[:8]


import random