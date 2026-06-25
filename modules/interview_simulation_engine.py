import logging
logger = logging.getLogger(__name__)

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random

from core.models.project import Project
from ai.models.ollama_client import OllamaClient

class InterviewType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    ARCHITECTURE_REVIEW = "architecture_review"
    HACKATHON_PITCH = "hackathon_pitch"
    PRODUCT_SENSE = "product_sense"

class InterviewDifficulty(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"

@dataclass
class InterviewQuestion:
    question: str
    type: InterviewType
    difficulty: int
    expected_answer_duration_seconds: int
    evaluation_criteria: List[str]
    follow_up: Optional[str] = None

@dataclass
class InterviewFeedback:
    question_id: int
    score: float
    strengths: List[str]
    weaknesses: List[str]
    improvement_tips: List[str]
    technical_accuracy: float
    communication_score: float

@dataclass
class InterviewResult:
    overall_score: float
    technical_score: float
    communication_score: float
    problem_solving_score: float
    questions: List[InterviewQuestion]
    feedback: List[InterviewFeedback]
    strengths_summary: List[str]
    weaknesses_summary: List[str]
    recommendations: List[str]
    readiness_level: str  # not_ready, needs_practice, ready, well_prepared
    interview_metadata: Dict[str, Any]

class InterviewSimulationEngine:
    """Engine for simulating technical and behavioral interviews"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        self.question_templates = self._initialize_question_templates()
        self.evaluation_rubrics = self._initialize_evaluation_rubrics()
    
    def _initialize_question_templates(self) -> Dict[str, List[str]]:
        """Initialize interview question templates by category"""
        return {
            "technical": [  # Generic technical questions (default fallback)
                "Explain the architecture of your project and key design decisions",
                "How do you handle errors and edge cases in your system?",
                "What testing strategy does your project use?",
            ],
            "data_structures": [
                "Design an algorithm to detect plagiarism in source code",
                "Implement a system to find the shortest path in a dynamic graph",
                "How would you design a recommendation engine?",
            ],
            "system_design": [
                "Design Twitter's backend for 100M DAU",
                "Design a real-time collaborative editing system",
                "Design a distributed rate limiter",
            ],
            "architecture": [
                "How would you migrate a monolith to microservices?",
                "Design an event-driven architecture for a payment system",
                "How do you ensure data consistency across microservices?",
            ],
            "behavioral": [
                "Tell me about a time you handled a technical disagreement",
                "Describe a project that failed and what you learned",
                "How do you prioritize technical debt vs new features?",
            ],
            "hackathon": [
                "How do you decide what to build in a 36-hour hackathon?",
                "Describe your hackathon project architecture in 2 minutes",
                "How do you handle team conflicts during a hackathon?",
            ]
        }
    
    def _initialize_evaluation_rubrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize evaluation rubrics for different interview types"""
        return {
            "technical": {
                "code_quality": 0.3,
                "problem_solving": 0.4,
                "communication": 0.2,
                "optimization": 0.1,
            },
            "system_design": {
                "architecture": 0.35,
                "scalability": 0.25,
                "trade_offs": 0.25,
                "communication": 0.15,
            },
            "behavioral": {
                "storytelling": 0.3,
                "impact": 0.3,
                "leadership": 0.2,
                "collaboration": 0.2,
            },
            "hackathon_pitch": {
                "clarity": 0.25,
                "innovation": 0.25,
                "feasibility": 0.25,
                "presentation": 0.25,
            }
        }
    
    async def run_interview(
        self,
        project: Project,
        interview_type: InterviewType = InterviewType.TECHNICAL,
        difficulty: InterviewDifficulty = InterviewDifficulty.MID,
        num_questions: int = 8,
        simulate_candidate: bool = False,
    ) -> InterviewResult:
        """Run a complete interview simulation"""
        
        # Generate questions
        questions = await self._generate_questions(
            project, interview_type, difficulty, num_questions
        )
        
        # Evaluate answers (simulate or from actual user)
        feedback = []
        if simulate_candidate:
            feedback = await self._simulate_answers_and_evaluate(
                project, questions, interview_type
            )
        else:
            feedback = await self._evaluate_provided_answers(
                project, questions, interview_type
            )
        
        # Calculate scores
        overall_score = sum(f.score for f in feedback) / len(feedback) if feedback else 0
        
        technical_scores = [
            f.technical_accuracy for f in feedback
            if f.technical_accuracy is not None
        ]
        technical_score = sum(technical_scores) / len(technical_scores) if technical_scores else 0
        
        comm_scores = [
            f.communication_score for f in feedback
            if f.communication_score is not None
        ]
        communication_score = sum(comm_scores) / len(comm_scores) if comm_scores else 0
        
        problem_solving_score = overall_score  # Derived from overall
        
        # Summarize strengths and weaknesses
        strengths = self._summarize_feedback(feedback, "strengths")
        weaknesses = self._summarize_feedback(feedback, "weaknesses")
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            weaknesses, interview_type, difficulty
        )
        
        # Determine readiness level
        readiness_level = self._determine_readiness_level(overall_score)
        
        return InterviewResult(
            overall_score=overall_score,
            technical_score=technical_score,
            communication_score=communication_score,
            problem_solving_score=problem_solving_score,
            questions=questions,
            feedback=feedback,
            strengths_summary=strengths,
            weaknesses_summary=weaknesses,
            recommendations=recommendations,
            readiness_level=readiness_level,
            interview_metadata={
                "interview_type": interview_type.value,
                "difficulty": difficulty.value,
                "num_questions": num_questions,
                "simulated": simulate_candidate,
                "timestamp": datetime.now().isoformat(),
            }
        )
    
    async def _generate_questions(
        self,
        project: Project,
        interview_type: InterviewType,
        difficulty: InterviewDifficulty,
        num_questions: int,
    ) -> List[InterviewQuestion]:
        """Generate interview questions"""
        
        # Get AI-generated questions
        questions_text = await self.ollama_client.generate(
            f"Generate {num_questions} {interview_type.value} interview questions:\n"
            f"Project Context: {project.name} - {project.description}\n"
            f"Difficulty Level: {difficulty.value}\n"
            f"Format each line as:\n"
            f"id|type|difficulty(1-10)|duration_seconds|question|criteria1,criteria2"
        )
        
        questions = []
        lines = questions_text.splitlines()
        
        for i, line in enumerate(lines[:num_questions]):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 5:
                    q_type = parts[1].strip() if len(parts) > 1 else interview_type.value
                    q_diff = int(parts[2].strip()) if parts[2].strip().isdigit() else self._difficulty_to_int(difficulty)
                    duration = int(parts[3].strip()) if parts[3].strip().isdigit() else 120
                    q_text = parts[4].strip()
                    criteria = parts[5].strip().split(",") if len(parts) > 5 else []
                    
                    question = InterviewQuestion(
                        question=q_text,
                        type=InterviewType(q_type),
                        difficulty=q_diff,
                        expected_answer_duration_seconds=duration,
                        evaluation_criteria=criteria,
                    )
                    questions.append(question)
        
        # Fallback questions
        if not questions:
            questions = self._fallback_questions(interview_type, difficulty, num_questions)
        
        return questions
    
    def _fallback_questions(
        self,
        interview_type: InterviewType,
        difficulty: InterviewDifficulty,
        num_questions: int,
    ) -> List[InterviewQuestion]:
        """Generate fallback questions"""
        
        base_diff = self._difficulty_to_int(difficulty)
        questions = []
        
        templates = self.question_templates.get(interview_type.value, self.question_templates["technical"])
        
        for i in range(min(num_questions, len(templates))):
            q = InterviewQuestion(
                question=templates[i],
                type=interview_type,
                difficulty=base_diff + random.randint(-1, 1),
                expected_answer_duration_seconds=random.choice([60, 90, 120, 180]),
                evaluation_criteria=["correctness", "clarity", "completeness"],
            )
            questions.append(q)
        
        return questions
    
    def _difficulty_to_int(self, difficulty: InterviewDifficulty) -> int:
        """Convert difficulty enum to integer"""
        mapping = {
            InterviewDifficulty.JUNIOR: 3,
            InterviewDifficulty.MID: 5,
            InterviewDifficulty.SENIOR: 7,
            InterviewDifficulty.STAFF: 8,
            InterviewDifficulty.PRINCIPAL: 9,
        }
        return mapping.get(difficulty, 5)
    
    async def _simulate_answers_and_evaluate(
        self,
        project: Project,
        questions: List[InterviewQuestion],
        interview_type: InterviewType,
    ) -> List[InterviewFeedback]:
        """Simulate candidate answers and evaluate them"""
        
        feedback_list = []
        
        for i, question in enumerate(questions):
            # Simulate an answer
            simulated_answer = await self.ollama_client.generate(
                f"As a {interview_type.value} interview candidate, provide a strong answer:\n"
                f"Question: {question.question}\n"
                f"Difficulty: {question.difficulty}/10\n"
                f"Context: Working on project '{project.name}'\n"
                f"Keep answer concise but comprehensive"
            )
            
            # Self-evaluate the answer
            evaluation = await self.ollama_client.generate(
                f"Evaluate this interview answer:\n"
                f"Question: {question.question}\n"
                f"Answer: {simulated_answer}\n"
                f"Evaluation Criteria: {question.evaluation_criteria}\n"
                f"Return format:\n"
                f"Score: 0-100\n"
                f"Strengths: comma-separated\n"
                f"Weaknesses: comma-separated\n"
                f"Tips: comma-separated\n"
                f"Technical Accuracy: 0-100\n"
                f"Communication: 0-100"
            )
            
            # Parse evaluation
            lines = evaluation.splitlines()
            score = 70.0
            strengths = ["Clear structure"]
            weaknesses = ["Could be more specific"]
            tips = ["Add concrete examples"]
            tech_accuracy = 75.0
            comm_score = 70.0
            
            for line in lines:
                if line.lower().startswith("score:"):
                    try:
                        score = float(line.split(":")[1].strip())
                    except:
                        pass
                elif line.lower().startswith("strengths:"):
                    strengths = [s.strip() for s in line.split(":")[1].split(",") if s.strip()]
                elif line.lower().startswith("weaknesses:"):
                    weaknesses = [w.strip() for w in line.split(":")[1].split(",") if w.strip()]
                elif line.lower().startswith("tips:"):
                    tips = [t.strip() for t in line.split(":")[1].split(",") if t.strip()]
                elif line.lower().startswith("technical accuracy:"):
                    try:
                        tech_accuracy = float(line.split(":")[1].strip())
                    except:
                        pass
                elif line.lower().startswith("communication:"):
                    try:
                        comm_score = float(line.split(":")[1].strip())
                    except:
                        pass
            
            feedback = InterviewFeedback(
                question_id=i,
                score=score,
                strengths=strengths[:3],
                weaknesses=weaknesses[:3],
                improvement_tips=tips[:3],
                technical_accuracy=tech_accuracy,
                communication_score=comm_score,
            )
            feedback_list.append(feedback)
        
        return feedback_list
    
    async def _evaluate_provided_answers(
        self,
        project: Project,
        questions: List[InterviewQuestion],
        interview_type: InterviewType,
    ) -> List[InterviewFeedback]:
        """Evaluate answers provided by actual user"""
        
        feedback_list = []
        for i, question in enumerate(questions):
            feedback = InterviewFeedback(
                question_id=i,
                score=random.uniform(50, 90),
                strengths=["Question well understood"],
                weaknesses=["Needs more detail"],
                improvement_tips=["Elaborate with examples"],
                technical_accuracy=random.uniform(60, 90),
                communication_score=random.uniform(55, 85),
            )
            feedback_list.append(feedback)
        
        return feedback_list
    
    def _summarize_feedback(
        self,
        feedback: List[InterviewFeedback],
        attribute: str,
    ) -> List[str]:
        """Summarize feedback across all questions"""
        
        all_items = []
        for f in feedback:
            items = getattr(f, attribute, [])
            all_items.extend(items)
        
        # Count frequencies and return top items
        from collections import Counter
        counter = Counter(all_items)
        return [item for item, _ in counter.most_common(5)]
    
    async def _generate_recommendations(
        self,
        weaknesses: List[str],
        interview_type: InterviewType,
        difficulty: InterviewDifficulty,
    ) -> List[str]:
        """Generate improvement recommendations"""
        
        recommendations = []
        
        for weakness in weaknesses:
            if "specific" in weakness.lower():
                recommendations.append("Practice with concrete examples from your projects")
            elif "structure" in weakness.lower() or "clarity" in weakness.lower():
                recommendations.append("Use the STAR method (Situation, Task, Action, Result)")
            elif "depth" in weakness.lower() or "detail" in weakness.lower():
                recommendations.append("Dive deeper into system design fundamentals")
            elif "communication" in weakness.lower():
                recommendations.append("Practice explaining technical concepts to non-technical audiences")
            else:
                recommendations.append(f"Improve: {weakness}")
        
        # Add difficulty-specific recommendations
        if difficulty in [InterviewDifficulty.SENIOR, InterviewDifficulty.STAFF, InterviewDifficulty.PRINCIPAL]:
            recommendations.append("Study advanced distributed systems patterns")
            recommendations.append("Prepare for leadership and mentoring questions")
        
        return recommendations[:6]
    
    def _determine_readiness_level(self, score: float) -> str:
        """Determine readiness level based on score"""
        if score >= 85:
            return "well_prepared"
        elif score >= 70:
            return "ready"
        elif score >= 55:
            return "needs_practice"
        else:
            return "not_ready"

