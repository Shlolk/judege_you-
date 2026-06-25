import logging
logger = logging.getLogger(__name__)

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
from collections import Counter

from core.models.project import Project
from ai.models.ollama_client import OllamaClient
from parsers.code_parser import CodeParser
from parsers.document_parser import DocumentParser

class WeaknessCategory(str, Enum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DESIGN = "design"
    INNOVATION = "innovation"
    BUSINESS = "business"
    TEAM = "team"

class WeaknessSeverity(str, Enum):
    CRITICAL = "critical"  # Will definitely cause failure
    HIGH = "high"  # Very likely to cause issues
    MEDIUM = "medium"  # Moderate concern
    LOW = "low"  # Minor issue, nice to fix

@dataclass
class Weakness:
    id: str
    category: WeaknessCategory
    title: str
    description: str
    severity: WeaknessSeverity
    impact_score: float  # 0-100
    location: Optional[str]  # File/module location
    root_cause: str
    symptoms: List[str]
    mitigation_steps: List[str]
    effort_to_fix: str  # minutes, hours, days
    exploitability: Optional[float]  # How easy to exploit (security)

@dataclass
class WeaknessReport:
    overall_weakness_score: float  # Higher = more weak
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    weaknesses: List[Weakness]
    category_breakdown: Dict[str, int]
    most_critical_weaknesses: List[Weakness]
    top_mitigation_priorities: List[str]
    risk_summary: str
    detected_at: datetime

class WeaknessDetectionEngine:
    """Engine for detecting weaknesses in projects"""
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        code_parser: CodeParser,
        document_parser: DocumentParser,
    ):
        self.ollama_client = ollama_client
        self.code_parser = code_parser
        self.document_parser = document_parser
        self.detection_patterns = self._initialize_detection_patterns()
    
    def _initialize_detection_patterns(self) -> Dict[str, List[str]]:
        """Initialize detection patterns for various weakness types"""
        return {
            "security": [
                r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]+['\"]",
                r"(?i)(exec|eval|system|popen|subprocess\.call)\s*\(",
                r"(?i)(sql|nosql|mongo|elastic)\s*\.\s*(find|query|execute)\s*\([^)]*\$",
                r"(?i)(allow[_-]?all|CORS[_-]?origin|access[_-]?control[_-]?allow[_-]?origin)\s*:\s*['\"]\*['\"]",
                r"(?i)(md5|sha1)\s*\(",
            ],
            "code_quality": [
                r"(?i)(TODO|FIXME|HACK|XXX|BUG)\b",
                r"(?i)(print|console\.log|System\.out\.print|debug)\s*\(",
                r"(?i)(except|catch)\s*(Exception|Error)\s*:?\s*(pass|return None|print)",
                r"if\s+False\s*:",
                r"commented[-_]?out|#.*TODO",
            ],
            "architecture": [
                r"import\s+\*\s*$",
                r"(?i)(god[-_]?class|god[_-]?object|blob)",
                r"(?i)(circular[_-]?import|circular[_-]?dependency)",
                r"(?i)(singleton|global[_-]?state)",
            ],
            "performance": [
                r"(?i)(for\s+.*\s+in\s+range\s*\(\s*len|for\s+i\s*,\s*.*\s+in\s+enumerate)",
                r"(?i)(\.\s*append\s*\(\s*.*\s+for\s+)",
                r"(?i)(nested\s+for|for.*for)",
                r"(?i)(while\s+True|while\s+1\s*:).*break",
            ]
        }
    
    async def detect_weaknesses(
        self,
        project: Project,
        categories: Optional[List[WeaknessCategory]] = None,
        deep_scan: bool = False,
    ) -> WeaknessReport:
        """Detect all weaknesses in the project"""
        
        if categories is None:
            categories = list(WeaknessCategory)
        
        all_weaknesses = []
        
        # Run different detection strategies in parallel
        import asyncio
        
        tasks = []
        if WeaknessCategory.ARCHITECTURE in categories:
            tasks.append(self._detect_architecture_weaknesses(project))
        if WeaknessCategory.SECURITY in categories:
            tasks.append(self._detect_security_weaknesses(project))
        if WeaknessCategory.PERFORMANCE in categories:
            tasks.append(self._detect_performance_weaknesses(project))
        if WeaknessCategory.DOCUMENTATION in categories:
            tasks.append(self._detect_documentation_weaknesses(project))
        if WeaknessCategory.TESTING in categories:
            tasks.append(self._detect_testing_weaknesses(project))
        if WeaknessCategory.MAINTAINABILITY in categories:
            tasks.append(self._detect_maintainability_weaknesses(project))
        if WeaknessCategory.DESIGN in categories:
            tasks.append(self._detect_design_weaknesses(project))
        if WeaknessCategory.INNOVATION in categories:
            tasks.append(self._detect_innovation_weaknesses(project))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            for result in results:
                all_weaknesses.extend(result)
        
        # Add AI-detected weaknesses
        if deep_scan:
            ai_weaknesses = await self._detect_ai_weaknesses(project)
            all_weaknesses.extend(ai_weaknesses)
        
        # Categorize and score
        critical = [w for w in all_weaknesses if w.severity == WeaknessSeverity.CRITICAL]
        high = [w for w in all_weaknesses if w.severity == WeaknessSeverity.HIGH]
        medium = [w for w in all_weaknesses if w.severity == WeaknessSeverity.MEDIUM]
        low = [w for w in all_weaknesses if w.severity == WeaknessSeverity.LOW]
        
        # Calculate overall weakness score (0-100, higher = more weak)
        overall_weakness_score = min(100, (
            len(critical) * 20 +
            len(high) * 10 +
            len(medium) * 5 +
            len(low) * 2
        ))
        
        # Category breakdown
        category_breakdown = Counter(w.category.value for w in all_weaknesses)
        
        # Top mitigation priorities
        top_mitigation = [
            w.mitigation_steps[0] if w.mitigation_steps else f"Fix {w.title}"
            for w in sorted(all_weaknesses, key=lambda x: x.impact_score, reverse=True)[:5]
        ]
        
        # Risk summary
        risk_summary = await self._generate_risk_summary(
            project, overall_weakness_score, critical, high
        )
        
        return WeaknessReport(
            overall_weakness_score=overall_weakness_score,
            critical_count=len(critical),
            high_count=len(high),
            medium_count=len(medium),
            low_count=len(low),
            weaknesses=all_weaknesses,
            category_breakdown=dict(category_breakdown),
            most_critical_weaknesses=critical[:5],
            top_mitigation_priorities=top_mitigation,
            risk_summary=risk_summary,
            detected_at=datetime.now(),
        )
    
    async def _detect_security_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect security weaknesses"""
        
        weaknesses = []
        
        # Check for hardcoded secrets
        secrets_found = self._scan_for_patterns(
            project, self.detection_patterns["security"]
        )
        
        for secret in secrets_found:
            weaknesses.append(Weakness(
                id=f"sec_{len(weaknesses)}",
                category=WeaknessCategory.SECURITY,
                title="Hardcoded Secret Detected",
                description=f"Potential secret found: {secret[:100]}",
                severity=WeaknessSeverity.CRITICAL,
                impact_score=95.0,
                location=secret.split(":")[0] if ":" in secret else None,
                root_cause="Secrets stored in code instead of environment variables",
                symptoms=["Credential exposure", "Unauthorized access risk"],
                mitigation_steps=["Move to environment variables", "Use a secrets manager"],
                effort_to_fix="minutes",
                exploitability=90.0,
            ))
        
        # Check for command injection vulnerabilities
        cmd_injection = self._scan_for_patterns(project, [
            r"(?i)(exec|eval|system|popen)\s*\(",
        ])
        for cmd in cmd_injection:
            weaknesses.append(Weakness(
                id=f"sec_cmd_{len(weaknesses)}",
                category=WeaknessCategory.SECURITY,
                title="Command Injection Risk",
                description=f"Potential command injection: {cmd[:100]}",
                severity=WeaknessSeverity.HIGH,
                impact_score=85.0,
                location=cmd.split(":")[0] if ":" in cmd else None,
                root_cause="Using shell execution without input sanitization",
                symptoms=["Remote code execution", "Server compromise"],
                mitigation_steps=["Use safe APIs", "Validate and sanitize all inputs"],
                effort_to_fix="hours",
                exploitability=75.0,
            ))
        
        return weaknesses
    
    async def _detect_architecture_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect architecture weaknesses"""
        
        weaknesses = []
        
        # Check for tight coupling / god classes
        coupling_issues = self._scan_for_patterns(
            project, self.detection_patterns["architecture"]
        )
        
        if coupling_issues:
            weaknesses.append(Weakness(
                id="arch_001",
                category=WeaknessCategory.ARCHITECTURE,
                title="Tight Coupling Detected",
                description="Multiple files show signs of tight coupling or god class anti-pattern",
                severity=WeaknessSeverity.HIGH,
                impact_score=75.0,
                location=coupling_issues[0].split(":")[0] if ":" in coupling_issues[0] else None,
                root_cause="Lack of modular design and separation of concerns",
                symptoms=["Hard to test", "Difficult to extend", "Changes cascade"],
                mitigation_steps=[
                    "Apply Single Responsibility Principle",
                    "Use dependency injection",
                    "Refactor into smaller modules"
                ],
                effort_to_fix="days",
                exploitability=40.0,
            ))
        
        return weaknesses
    
    async def _detect_performance_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect performance weaknesses"""
        
        weaknesses = []
        
        # Check for O(n^2) patterns
        perf_issues = self._scan_for_patterns(
            project, self.detection_patterns["performance"]
        )
        
        if perf_issues:
            weaknesses.append(Weakness(
                id="perf_001",
                category=WeaknessCategory.PERFORMANCE,
                title="Inefficient Looping Pattern",
                description="Nested loops or inefficient iteration patterns detected",
                severity=WeaknessSeverity.MEDIUM,
                impact_score=55.0,
                location=perf_issues[0].split(":")[0] if ":" in perf_issues[0] else None,
                root_cause="Using O(n^2) algorithms where O(n) would suffice",
                symptoms=["Slow response times", "High CPU usage"],
                mitigation_steps=["Use hash maps for lookups", "Optimize loops", "Cache results"],
                effort_to_fix="hours",
                exploitability=30.0,
            ))
        
        return weaknesses
    
    async def _detect_documentation_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect documentation weaknesses"""
        
        weaknesses = []
        
        # Check for missing/insufficient documentation
        has_readme = False
        has_api_docs = False
        has_architecture_docs = False
        
        try:
            import os
            for root, dirs, files in os.walk(getattr(project, "local_path", ".")):
                for f in files:
                    if f.lower() == "readme.md":
                        has_readme = True
                    elif f.lower() in ["api.md", "api_docs.md", "swagger"]:
                        has_api_docs = True
                    elif f.lower() in ["architecture.md", "arch.md", "design.md"]:
                        has_architecture_docs = True
        except:
            pass
        
        if not has_readme:
            weaknesses.append(Weakness(
                id="doc_001",
                category=WeaknessCategory.DOCUMENTATION,
                title="Missing README",
                description="No README.md found in the project root",
                severity=WeaknessSeverity.MEDIUM,
                impact_score=40.0,
                location="root",
                root_cause="Documentation not prioritized",
                symptoms=["New contributors struggle", "Unclear project purpose"],
                mitigation_steps=["Create comprehensive README.md"],
                effort_to_fix="hours",
                exploitability=10.0,
            ))
        
        if not has_api_docs and not has_architecture_docs:
            weaknesses.append(Weakness(
                id="doc_002",
                category=WeaknessCategory.DOCUMENTATION,
                title="Missing Technical Documentation",
                description="No API or architecture documentation found",
                severity=WeaknessSeverity.MEDIUM,
                impact_score=35.0,
                location="docs/",
                root_cause="Documentation deferred or not prioritized",
                symptoms=["Difficult onboarding", "Knowledge silos"],
                mitigation_steps=[
                    "Create API documentation",
                    "Document architecture decisions (ADRs)"
                ],
                effort_to_fix="days",
                exploitability=15.0,
            ))
        
        return weaknesses
    
    async def _detect_testing_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect testing weaknesses"""
        
        weaknesses = []
        
        test_files_found = 0
        total_files = 1  # Avoid division by zero
        
        try:
            import os
            project_path = getattr(project, "local_path", ".")
            all_files = []
            test_files = []
            
            for root, dirs, files in os.walk(project_path):
                for f in files:
                    all_files.append(f)
                    if "test" in f.lower() or "spec" in f.lower() or "test_" in f:
                        test_files_found += 1
            
            total_files = max(1, len(all_files))
        except:
            pass
        
        test_coverage = (test_files_found / max(1, total_files)) * 100
        
        if test_files_found == 0:
            weaknesses.append(Weakness(
                id="test_001",
                category=WeaknessCategory.TESTING,
                title="No Tests Found",
                description="Zero test files detected in the codebase",
                severity=WeaknessSeverity.CRITICAL,
                impact_score=90.0,
                location="tests/",
                root_cause="Testing not part of development workflow",
                symptoms=["Untested code", "Regression bugs"],
                mitigation_steps=[
                    "Set up pytest framework",
                    "Write unit tests for core functionality",
                    "Set minimum 60% test coverage target"
                ],
                effort_to_fix="days",
                exploitability=50.0,
            ))
        elif test_coverage < 20:
            weaknesses.append(Weakness(
                id="test_002",
                category=WeaknessCategory.TESTING,
                title="Insufficient Test Coverage",
                description=f"Only {test_coverage:.1f}% of files have corresponding tests",
                severity=WeaknessSeverity.HIGH,
                impact_score=70.0,
                location="tests/",
                root_cause="Testing added after development",
                symptoms=["Bug-prone modules", "Slow development velocity"],
                mitigation_steps=[
                    "Increase test coverage to >60%",
                    "Add CI pipeline with test automation"
                ],
                effort_to_fix="days",
                exploitability=35.0,
            ))
        
        return weaknesses
    
    async def _detect_maintainability_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect maintainability weaknesses"""
        
        weaknesses = []
        
        # Check for TODO/FIXME comments
        todo_patterns = self._scan_for_patterns(
            project, self.detection_patterns["code_quality"]
        )
        
        if len(todo_patterns) > 5:
            weaknesses.append(Weakness(
                id="maint_001",
                category=WeaknessCategory.MAINTAINABILITY,
                title=f"High Number of Unresolved TODOs ({len(todo_patterns)})",
                description=f"Found {len(todo_patterns)} TODO/FIXME/HACK comments",
                severity=WeaknessSeverity.MEDIUM,
                impact_score=45.0,
                location="Various files",
                root_cause="Technical debt accumulation",
                symptoms=["Hidden bugs", "Incomplete features"],
                mitigation_steps=[
                    "Audit all TODO comments",
                    "Create JIRA/issue for each",
                    "Set aside time to address"
                ],
                effort_to_fix="days",
                exploitability=25.0,
            ))
        
        # Check for bare except clauses
        except_patterns = self._scan_for_patterns(project, [
            r"(?i)(except|catch)\s*(Exception|Error)\s*:?\s*(pass|return None|print)",
        ])
        
        if except_patterns:
            weaknesses.append(Weakness(
                id="maint_002",
                category=WeaknessCategory.MAINTAINABILITY,
                title="Bare Exception Handlers",
                description="Found exception handlers that silently catch all exceptions",
                severity=WeaknessSeverity.HIGH,
                impact_score=65.0,
                location=except_patterns[0].split(":")[0] if ":" in except_patterns[0] else None,
                root_cause="Error handling not properly implemented",
                symptoms=["Silent failures", "Hard to debug errors"],
                mitigation_steps=[
                    "Catch specific exceptions",
                    "Add proper error logging",
                    "Implement proper error recovery"
                ],
                effort_to_fix="hours",
                exploitability=20.0,
            ))
        
        return weaknesses
    
    async def _detect_design_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect design weaknesses"""
        
        weaknesses = []
        
        # Check design patterns usage
        design_analysis = await self.ollama_client.generate(
            f"Analyze design weaknesses in this project:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Return: Identify 1-3 design pattern weaknesses or anti-patterns"
        )
        
        if design_analysis and len(design_analysis) > 50:
            weaknesses.append(Weakness(
                id="design_001",
                category=WeaknessCategory.DESIGN,
                title="Design Pattern Issues Detected",
                description=design_analysis[:200],
                severity=WeaknessSeverity.MEDIUM,
                impact_score=50.0,
                location="Various",
                root_cause="Inconsistent application of design patterns",
                symptoms=["Code inconsistency", "Maintenance challenges"],
                mitigation_steps=[
                    "Review and apply consistent design patterns",
                    "Document architecture decisions"
                ],
                effort_to_fix="days",
                exploitability=20.0,
            ))
        
        return weaknesses
    
    async def _detect_innovation_weaknesses(self, project: Project) -> List[Weakness]:
        """Detect innovation-related weaknesses"""
        
        weaknesses = []
        
        innovation_analysis = await self.ollama_client.generate(
            f"Analyze innovation weaknesses in this project:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Determine if this project is a 'ChatGPT wrapper'\n"
            f"Return: Innovation score (0-100), weaknesses as comma-separated list"
        )
        
        # Check for common "wrapper" patterns
        is_wrapper = any(
            keyword in project.description.lower()
            for keyword in ["gpt", "llm", "ai-powered", "chatbot"]
        ) if project.description else False
        
        if is_wrapper:
            weaknesses.append(Weakness(
                id="innov_001",
                category=WeaknessCategory.INNOVATION,
                title="Potential ChatGPT Wrapper",
                description="Project may be overly dependent on LLM APIs without unique value",
                severity=WeaknessSeverity.HIGH,
                impact_score=80.0,
                location="Core logic",
                root_cause="Lack of proprietary technology or unique data",
                symptoms=["Easy to replicate", "Low barrier to entry"],
                mitigation_steps=[
                    "Add proprietary algorithms",
                    "Create unique dataset",
                    "Build defensible technology"
                ],
                effort_to_fix="weeks",
                exploitability=70.0,
            ))
        
        return weaknesses
    
    async def _detect_ai_weaknesses(self, project: Project) -> List[Weakness]:
        """Use AI to detect additional weaknesses"""
        
        weaknesses = []
        
        # Comprehensive AI scan
        ai_scan = await self.ollama_client.generate(
            f"Perform a comprehensive weakness scan on this project:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Repository: {project.repository_url or 'Local'}\n\n"
            f"Identify 5-10 potential weaknesses not easily caught by static analysis.\n"
            f"For each weakness provide:\n"
            f"Category|Title|Severity(critical/high/medium/low)|Description|Mitigation"
        )
        
        lines = ai_scan.splitlines()
        for line in lines:
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    category = parts[0].strip().lower()
                    title = parts[1].strip()
                    severity_str = parts[2].strip().lower()
                    description = parts[3].strip()
                    
                    # Map severity
                    severity_map = {
                        "critical": WeaknessSeverity.CRITICAL,
                        "high": WeaknessSeverity.HIGH,
                        "medium": WeaknessSeverity.MEDIUM,
                        "low": WeaknessSeverity.LOW,
                    }
                    severity = severity_map.get(severity_str, WeaknessSeverity.MEDIUM)
                    
                    # Map category
                    try:
                        cat = WeaknessCategory(category)
                    except ValueError:
                        cat = WeaknessCategory.ARCHITECTURE
                    
                    weaknesses.append(Weakness(
                        id=f"ai_{len(weaknesses)}",
                        category=cat,
                        title=title,
                        description=description[:200],
                        severity=severity,
                        impact_score=self._severity_to_score(severity),
                        location="AI-detected",
                        root_cause=description[:100],
                        symptoms=["Potential issue"],
                        mitigation_steps=[parts[4].strip()] if len(parts) > 4 else ["Investigate further"],
                        effort_to_fix="unknown",
                        exploitability=self._severity_to_exploitability(severity),
                    ))
        
        return weaknesses
    
    def _scan_for_patterns(
        self,
        project: Project,
        patterns: List[str],
    ) -> List[str]:
        """Scan project files for regex patterns"""
        
        matches = []
        import os
        
        project_path = getattr(project, "local_path", ".")
        if not os.path.exists(project_path):
            return matches
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Skip hidden dirs and common non-source dirs
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs', '.jsx', '.tsx')):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                for pattern in patterns:
                                    for match in re.finditer(pattern, content):
                                        line_num = content[:match.start()].count('\n') + 1
                                        matches.append(f"{filepath}:{line_num}:{match.group()[:80]}")
                        except:
                            continue
        except:
            pass
        
        return matches
    
    def _severity_to_score(self, severity: WeaknessSeverity) -> float:
        """Convert severity to impact score"""
        mapping = {
            WeaknessSeverity.CRITICAL: 90.0,
            WeaknessSeverity.HIGH: 70.0,
            WeaknessSeverity.MEDIUM: 50.0,
            WeaknessSeverity.LOW: 20.0,
        }
        return mapping.get(severity, 50.0)
    
    def _severity_to_exploitability(self, severity: WeaknessSeverity) -> float:
        """Convert severity to exploitability score"""
        mapping = {
            WeaknessSeverity.CRITICAL: 85.0,
            WeaknessSeverity.HIGH: 65.0,
            WeaknessSeverity.MEDIUM: 40.0,
            WeaknessSeverity.LOW: 15.0,
        }
        return mapping.get(severity, 40.0)
    
    async def _generate_risk_summary(
        self,
        project: Project,
        overall_score: float,
        critical: List[Weakness],
        high: List[Weakness],
    ) -> str:
        """Generate a concise risk summary"""
        
        if overall_score >= 70:
            return f"CRITICAL: Project has {len(critical)} critical and {len(high)} high-severity weaknesses. Immediate action required."
        elif overall_score >= 50:
            return f"HIGH: Project has {len(critical)} critical and {len(high)} high-severity weaknesses. Schedule remediation."
        elif overall_score >= 30:
            return f"MODERATE: Project weaknesses are manageable but should be addressed in next sprint."
        else:
            return f"LOW: Project is in good shape with minor weaknesses detected."

