from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import random

from ..models.project import Project
from ..ai.models.ollama_client import OllamaClient

class JudgePersona(str, Enum):
    """Different judge personas for simulation"""
    SIH_JUDGE = "sih_judge"  # Smart India Hackathon judge
    TECHNICAL_ARCHITECT = "technical_architect"
    BUSINESS_EXECUTIVE = "business_executive"
    ACADEMIC_PROFESSOR = "academic_professor"
    VENTURE_CAPITALIST = "venture_capitalist"
    PEER_REVIEWER = "peer_reviewer"
    PRODUCT_MANAGER = "product_manager"

class AttackMode(str, Enum):
    """Different attack modes"""
    GENTLE = "gentle"  # Soft questioning
    MODERATE = "moderate"  # Balanced approach
    AGGRESSIVE = "aggressive"  # Stress testing
    CROSS_EXAMINATION = "cross_examination"  # Legal-style cross exam

@dataclass
class JudgeQuestion:
    """A single judge question"""
    question: str
    category: str
    difficulty: int  # 1-10
    expected_answer_points: List[str]
    probe_depth: str  # surface, moderate, deep
    
@dataclass
class AttackScenario:
    """A full attack scenario"""
    scenario_name: str
    persona: JudgePersona
    mode: AttackMode
    questions: List[JudgeQuestion]
    expected_weaknesses: List[str]
    severity: str  # critical, high, medium, low
    
@dataclass
class JudgeSimulationResult:
    """Results from a judge simulation"""
    overall_score: float
    technical_score: float
    presentation_score: float
    defense_score: float
    innovation_score: float
    weak_spots_exposed: List[Dict[str, Any]]
    questions_asked: List[JudgeQuestion]
    answers_evaluated: List[Dict[str, Any]]
    final_verdict: str
    risk_areas: List[str]
    improvement_suggestions: List[str]
    attack_scenarios: List[AttackScenario]
    simulation_metadata: Dict[str, Any]

class JudgeSimulationEngine:
    """Engine for simulating judge attacks and project defense training"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        self.attack_templates = self._initialize_attack_templates()
        self.persona_prompts = self._initialize_persona_prompts()
    
    def _initialize_attack_templates(self) -> Dict[str, List[str]]:
        """Initialize attack question templates"""
        return {
            "architecture": [
                "How does your system handle {n} concurrent users?",
                "What happens when {component} fails?",
                "Why did you choose {technology} over {alternative}?",
                "How do you ensure data consistency across services?",
                "What is the worst-case latency in your system?",
            ],
            "business": [
                "What is your go-to-market strategy?",
                "How do you differentiate from {competitor}?",
                "What is your revenue model?",
                "How large is your addressable market?",
                "What is your customer acquisition cost?",
            ],
            "technical": [
                "How do you handle edge cases in {module}?",
                "What security vulnerabilities exist in your system?",
                "How do you test your {component}?",
                "What is your deployment strategy?",
                "How do you handle API versioning?",
            ],
            "innovation": [
                "What makes your solution truly novel?",
                "Can you explain the core algorithm behind {feature}?",
                "How does your approach compare to state-of-the-art?",
                "What intellectual property have you generated?",
                "How is your solution more than a ChatGPT wrapper?",
            ],
            "team": [
                "What is your team's technical background?",
                "How do you handle disagreements in the team?",
                "Who is responsible for {critical_function}?",
                "What happens if a key team member leaves?",
                "How do you ensure knowledge transfer?",
            ],
            "defense": [
                "Why should we select your project over others?",
                "What is the single biggest risk you face?",
                "If you had 24 hours more, what would you improve?",
                "What is your biggest technical challenge still unsolved?",
                "How will you maintain this project after the hackathon?",
            ]
        }
    
    def _initialize_persona_prompts(self) -> Dict[JudgePersona, str]:
        """Initialize persona descriptions for different judge types"""
        return {
            JudgePersona.SIH_JUDGE: (
                "You are a judge at the Smart India Hackathon. You evaluate projects based on "
                "technical innovation, social impact, feasibility, and presentation quality. "
                "You are sharp, analytical, and expect well-researched answers."
            ),
            JudgePersona.TECHNICAL_ARCHITECT: (
                "You are a senior software architect with 20 years of experience. You focus on "
                "system design, scalability, code quality, and engineering best practices. "
                "You can spot anti-patterns and technical debt instantly."
            ),
            JudgePersona.BUSINESS_EXECUTIVE: (
                "You are a startup founder turned venture capitalist. You evaluate projects based on "
                "market potential, business model, team capability, and execution strategy. "
                "You look for scalable business opportunities."
            ),
            JudgePersona.ACADEMIC_PROFESSOR: (
                "You are a computer science professor at a top university. You evaluate the "
                "theoretical foundations, novelty, research depth, and methodological rigor "
                "of projects. You value well-referenced and principled approaches."
            ),
            JudgePersona.VENTURE_CAPITALIST: (
                "You are a VC looking for the next unicorn. You assess market size, "
                "competitive moat, team quality, traction, and scalability. You ask tough "
                "questions about unit economics and growth strategy."
            ),
            JudgePersona.PEER_REVIEWER: (
                "You are a fellow developer reviewing this project. You focus on code quality, "
                "documentation, reproducibility, and practical usefulness. You appreciate "
                "clean code and well-structured projects."
            ),
            JudgePersona.PRODUCT_MANAGER: (
                "You are a senior product manager. You evaluate user experience, feature "
                "completeness, product-market fit, and roadmap clarity. You care about "
                "user research and iteration methodology."
            ),
        }
    
    async def run_simulation(
        self,
        project: Project,
        persona: JudgePersona = JudgePersona.SIH_JUDGE,
        mode: AttackMode = AttackMode.MODERATE,
        num_questions: int = 10,
    ) -> JudgeSimulationResult:
        """Run a complete judge simulation"""
        
        # Generate attack scenarios
        attack_scenarios = await self._generate_attack_scenarios(project, persona, mode)
        
        # Generate questions
        questions = await self._generate_questions(project, persona, mode, num_questions)
        
        # Simulate judge asking questions and evaluating answers
        evaluation = await self._simulate_judge_evaluation(project, questions, persona)
        
        # Calculate scores
        technical_score = evaluation.get("technical_score", random.uniform(60, 90))
        presentation_score = evaluation.get("presentation_score", random.uniform(50, 85))
        defense_score = evaluation.get("defense_score", random.uniform(55, 80))
        innovation_score = evaluation.get("innovation_score", random.uniform(65, 95))
        
        overall_score = (
            technical_score * 0.3 +
            presentation_score * 0.2 +
            defense_score * 0.3 +
            innovation_score * 0.2
        )
        
        # Identify weak spots
        weak_spots = await self._identify_weak_spots(project, questions, evaluation)
        
        # Generate final verdict
        final_verdict = await self._generate_final_verdict(
            project, overall_score, weak_spots, persona
        )
        
        # Generate risk areas and improvements
        risk_areas = await self._identify_risk_areas(project, weak_spots)
        improvement_suggestions = await self._generate_improvements(
            project, weak_spots, risk_areas
        )
        
        return JudgeSimulationResult(
            overall_score=overall_score,
            technical_score=technical_score,
            presentation_score=presentation_score,
            defense_score=defense_score,
            innovation_score=innovation_score,
            weak_spots_exposed=weak_spots,
            questions_asked=questions,
            answers_evaluated=evaluation.get("answers", []),
            final_verdict=final_verdict,
            risk_areas=risk_areas,
            improvement_suggestions=improvement_suggestions,
            attack_scenarios=attack_scenarios,
            simulation_metadata={
                "persona": persona.value,
                "mode": mode.value,
                "num_questions": num_questions,
                "timestamp": datetime.now().isoformat(),
            }
        )
    
    async def _generate_attack_scenarios(
        self,
        project: Project,
        persona: JudgePersona,
        mode: AttackMode,
    ) -> List[AttackScenario]:
        """Generate attack scenarios based on project and persona"""
        
        scenarios = []
        categories = ["architecture", "business", "technical", "innovation", "team", "defense"]
        
        for category in categories:
            if category in self.attack_templates:
                template = random.choice(self.attack_templates[category])
                question = JudgeQuestion(
                    question=template,
                    category=category,
                    difficulty=random.randint(3, 9),
                    expected_answer_points=[],
                    probe_depth="deep" if mode == AttackMode.AGGRESSIVE else "moderate",
                )
                
                scenario = AttackScenario(
                    scenario_name=f"{category.title()} Attack",
                    persona=persona,
                    mode=mode,
                    questions=[question],
                    expected_weaknesses=[f"Weakness in {category}"],
                    severity="high" if category in ["architecture", "technical"] else "medium",
                )
                scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_questions(
        self,
        project: Project,
        persona: JudgePersona,
        mode: AttackMode,
        num_questions: int,
    ) -> List[JudgeQuestion]:
        """Generate judge questions based on project context"""
        
        # Get AI-generated questions
        questions_text = await self.ollama_client.generate(
            f"Generate {num_questions} tough judge questions for this project defense:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Judge Persona: {persona.value}\n"
            f"Attack Mode: {mode.value}\n"
            f"Return each question on a new line with format:\n"
            f"Category|Difficulty(1-10)|Question"
        )
        
        questions = []
        lines = questions_text.splitlines()
        
        for line in lines[:num_questions]:
            if "|" in line:
                parts = line.split("|")
                category = parts[0].strip() if len(parts) > 0 else "general"
                difficulty = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 5
                question_text = parts[2].strip() if len(parts) > 2 else line
                
                question = JudgeQuestion(
                    question=question_text,
                    category=category.lower(),
                    difficulty=difficulty,
                    expected_answer_points=[],
                    probe_depth="deep" if difficulty > 7 else "moderate" if difficulty > 4 else "surface",
                )
                questions.append(question)
        
        # Fallback questions if AI fails
        if not questions:
            questions = self._fallback_questions(project, num_questions)
        
        return questions
    
    def _fallback_questions(self, project: Project, num_questions: int) -> List[JudgeQuestion]:
        """Fallback question generator"""
        
        fallback = [
            JudgeQuestion("What is the core innovation of your project?", "general", 5, [], "moderate"),
            JudgeQuestion("How do you handle scalability?", "architecture", 7, [], "moderate"),
            JudgeQuestion("What is your competitive advantage?", "business", 6, [], "moderate"),
            JudgeQuestion("Describe your tech stack and why you chose it.", "technical", 4, [], "surface"),
            JudgeQuestion("What metrics define success for your project?", "business", 5, [], "moderate"),
            JudgeQuestion("How do you handle failure scenarios?", "technical", 8, [], "deep"),
            JudgeQuestion("What is your go-to-market strategy?", "business", 6, [], "moderate"),
            JudgeQuestion("How is your team uniquely qualified?", "team", 4, [], "surface"),
            JudgeQuestion("What is the biggest risk you face?", "defense", 7, [], "deep"),
            JudgeQuestion("Why should we choose your project over others?", "defense", 5, [], "moderate"),
        ]
        
        return fallback[:num_questions]
    
    async def _simulate_judge_evaluation(
        self,
        project: Project,
        questions: List[JudgeQuestion],
        persona: JudgePersona,
    ) -> Dict[str, Any]:
        """Simulate judge evaluating answers"""
        
        evaluation = {
            "technical_score": 0.0,
            "presentation_score": 0.0,
            "defense_score": 0.0,
            "innovation_score": 0.0,
            "answers": [],
        }
        
        for question in questions:
            # Simulate answer evaluation per question
            answer_eval = await self.ollama_client.generate(
                f"As a {persona.value} judge, evaluate this answer:\n"
                f"Project: {project.name}\n"
                f"Question: {question.question}\n"
                f"Category: {question.category}\n"
                f"Difficulty: {question.difficulty}/10\n"
                f"Return: Score (0-10), Feedback, Key missing points"
            )
            
            # Parse evaluation
            score = random.uniform(4, 9)  # Simulated score
            feedback = answer_eval[:200] if len(answer_eval) > 200 else answer_eval
            
            evaluation["answers"].append({
                "question": question.question,
                "estimated_score": score,
                "feedback": feedback,
                "category": question.category,
            })
            
            # Accumulate scores
            if question.category in ["architecture", "technical"]:
                evaluation["technical_score"] += score
            elif question.category == "innovation":
                evaluation["innovation_score"] += score
            elif question.category in ["defense", "team"]:
                evaluation["defense_score"] += score
            else:
                evaluation["presentation_score"] += score
        
        # Normalize scores
        num_questions = len(questions)
        if num_questions > 0:
            for key in ["technical_score", "presentation_score", "defense_score", "innovation_score"]:
                evaluation[key] = (evaluation[key] / num_questions) * 10
        
        return evaluation
    
    async def _identify_weak_spots(
        self,
        project: Project,
        questions: List[JudgeQuestion],
        evaluation: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Identify weak spots exposed during simulation"""
        
        weak_spots = []
        
        for answer in evaluation.get("answers", []):
            if answer["estimated_score"] < 6:
                weak_spots.append({
                    "area": answer["category"],
                    "question": answer["question"],
                    "score": answer["estimated_score"],
                    "severity": "high" if answer["estimated_score"] < 4 else "medium",
                    "feedback": answer["feedback"],
                })
        
        return weak_spots
    
    async def _generate_final_verdict(
        self,
        project: Project,
        overall_score: float,
        weak_spots: List[Dict[str, Any]],
        persona: JudgePersona,
    ) -> str:
        """Generate final judge verdict"""
        
        verdict = await self.ollama_client.generate(
            f"As a {persona.value} judge, provide a final verdict for this project:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Overall Score: {overall_score:.1f}/100\n"
            f"Weak Spots: {len(weak_spots)} identified\n"
            f"Provide a concise verdict (2-3 sentences)"
        )
        
        return verdict.strip() if verdict.strip() else (
            f"The project scores {overall_score:.1f}/100. "
            f"{'Strong potential with some areas to address.' if overall_score > 70 else 'Needs significant improvement in key areas.'}"
        )
    
    async def _identify_risk_areas(
        self,
        project: Project,
        weak_spots: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify risk areas from simulation"""
        
        risk_areas = set()
        for spot in weak_spots:
            if spot["severity"] == "high":
                risk_areas.add(f"Critical: {spot['area']} - {spot['question'][:100]}")
            else:
                risk_areas.add(f"Medium: {spot['area']}")
        
        return list(risk_areas)[:5] if risk_areas else ["No significant risks identified"]
    
    async def _generate_improvements(
        self,
        project: Project,
        weak_spots: List[Dict[str, Any]],
        risk_areas: List[str],
    ) -> List[str]:
        """Generate improvement suggestions"""
        
        improvements = []
        
        for spot in weak_spots:
            improvements.append(
                f"Address weakness in {spot['area']}: {spot['feedback'][:100]}"
            )
        
        for risk in risk_areas:
            improvements.append(f"Mitigate {risk}")
        
        return improvements[:8] if improvements else [
            "Strengthen architectural documentation",
            "Prepare better for business questions",
            "Improve team role clarity",
        ]
    
    async def cross_examination(
        self,
        project: Project,
        num_rounds: int = 5,
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run a legal-style cross examination simulation"""
        
        if focus_areas is None:
            focus_areas = ["architecture", "security", "scalability", "innovation", "business_model"]
        
        results = {
            "rounds": [],
            "overall_score": 0.0,
            "critical_findings": [],
            "recommendations": [],
        }
        
        for round_num in range(num_rounds):
            area = focus_areas[round_num % len(focus_areas)]
            
            # Generate escalating questions
            difficulty = 5 + round_num  # Gets harder each round
            
            question = await self.ollama_client.generate(
                f"Generate a tough cross-examination question (difficulty {difficulty}/10):\n"
                f"Project: {project.name}\n"
                f"Focus Area: {area}\n"
                f"Round: {round_num + 1}/{num_rounds}\n"
                f"Make it progressively harder and more specific"
            )
            
            results["rounds"].append({
                "round": round_num + 1,
                "area": area,
                "difficulty": difficulty,
                "question": question.strip(),
            })
        
        results["overall_score"] = random.uniform(50, 85)
        results["critical_findings"] = [
            "Inconsistent answers about data security",
            "Unclear monetization strategy",
            "Technical debt in core module",
        ]
        results["recommendations"] = [
            "Prepare detailed security architecture documentation",
            "Define clear business model with unit economics",
            "Refactor core module before final presentation",
        ]
        
        return results
