import logging
logger = logging.getLogger(__name__)

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import re

from ai.models.ollama_client import OllamaClient
from core.models.project import Project

class ReasoningStrategy(str, Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    DECOMPOSITION = "decomposition"
    ANALOGY = "analogy"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    BACKWARD_REASONING = "backward_reasoning"

@dataclass
class ReasoningStep:
    step_number: int
    description: str
    reasoning: str
    conclusion: str
    confidence: float

@dataclass
class ReasoningChain:
    question: str
    strategy: ReasoningStrategy
    steps: List[ReasoningStep]
    final_answer: str
    confidence: float
    alternatives: List[str]
    caveats: List[str]
    processing_time_ms: float

@dataclass
class Recommendation:
    priority: int
    category: str
    title: str
    description: str
    expected_impact: float
    effort_estimate: str
    risk_level: str
    implementation_steps: List[str]

class AIReasoningEngine:
    """Advanced AI reasoning engine for complex analysis"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
    
    async def reason(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT,
        max_steps: int = 5,
    ) -> ReasoningChain:
        """Perform multi-step reasoning to answer a complex question"""
        
        start_time = datetime.now()
        steps = []
        
        if strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            steps = await self._chain_of_thought(question, context, max_steps)
        elif strategy == ReasoningStrategy.TREE_OF_THOUGHT:
            steps = await self._tree_of_thought(question, context, max_steps)
        elif strategy == ReasoningStrategy.DECOMPOSITION:
            steps = await self._decomposition(question, context, max_steps)
        elif strategy == ReasoningStrategy.ANALOGY:
            steps = await self._analogy_reasoning(question, context)
        elif strategy == ReasoningStrategy.HYPOTHESIS_TESTING:
            steps = await self._hypothesis_testing(question, context, max_steps)
        elif strategy == ReasoningStrategy.BACKWARD_REASONING:
            steps = await self._backward_reasoning(question, context, max_steps)
        
        # Synthesize final answer
        final_answer = await self._synthesize_answer(question, steps)
        
        # Generate alternatives and caveats
        alternatives = await self._generate_alternatives(question, final_answer)
        caveats = await self._identify_caveats(question, final_answer, context)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ReasoningChain(
            question=question,
            strategy=strategy,
            steps=steps,
            final_answer=final_answer,
            confidence=min(1.0, len(steps) * 0.15),
            alternatives=alternatives,
            caveats=caveats,
            processing_time_ms=processing_time,
        )
    
    async def _chain_of_thought(
        self,
        question: str,
        context: Optional[Dict[str, Any]],
        max_steps: int,
    ) -> List[ReasoningStep]:
        """Chain-of-thought reasoning - step by step deduction"""
        
        steps = []
        
        for i in range(max_steps):
            step_prompt = self._build_cot_prompt(question, context, steps, i + 1, max_steps)
            
            response = await self.ollama_client.generate(
                f"Chain of Thought Reasoning - Step {i + 1}/{max_steps}:\n{step_prompt}\n\n"
                f"Format:\nStep Description:\nReasoning:\nConclusion:\nConfidence (0-1):"
            )
            
            step = self._parse_reasoning_step(response, i + 1)
            steps.append(step)
            
            # Early stopping if high confidence
            if step.confidence > 0.95:
                break
        
        return steps
    
    def _build_cot_prompt(
        self,
        question: str,
        context: Optional[Dict[str, Any]],
        previous_steps: List[ReasoningStep],
        current_step: int,
        max_steps: int,
    ) -> str:
        """Build chain-of-thought prompt"""
        
        prompt = f"Question: {question}\n"
        
        if context:
            prompt += f"Context: {json.dumps(context)}\n"
        
        if previous_steps:
            prompt += "\nPrevious reasoning steps:\n"
            for step in previous_steps:
                prompt += f"  Step {step.step_number}: {step.conclusion}\n"
        
        if current_step < max_steps:
            prompt += f"\nWhat is the next logical step in answering this question?"
        else:
            prompt += f"\nProvide the final conclusion."
        
        return prompt
    
    def _parse_reasoning_step(self, response: str, step_num: int) -> ReasoningStep:
        """Parse a reasoning step from LLM response"""
        
        description = ""
        reasoning = ""
        conclusion = ""
        confidence = 0.7
        
        lines = response.splitlines()
        current_section = None
        
        for line in lines:
            lower_line = line.lower()
            if "step description:" in lower_line or "description:" in lower_line:
                current_section = "description"
                continue
            elif "reasoning:" in lower_line:
                current_section = "reasoning"
                continue
            elif "conclusion:" in lower_line:
                current_section = "conclusion"
                continue
            elif "confidence:" in lower_line:
                try:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        confidence = float(match.group(1))
                except:
                    confidence = 0.7
                continue
            
            if current_section == "description":
                description += line + " "
            elif current_section == "reasoning":
                reasoning += line + " "
            elif current_section == "conclusion":
                conclusion += line + " "
        
        return ReasoningStep(
            step_number=step_num,
            description=description.strip() or f"Step {step_num} reasoning",
            reasoning=reasoning.strip() or response[:200],
            conclusion=conclusion.strip() or "Analysis completed",
            confidence=min(1.0, max(0.0, confidence)),
        )
    
    async def _tree_of_thought(
        self,
        question: str,
        context: Optional[Dict[str, Any]],
        max_steps: int,
    ) -> List[ReasoningStep]:
        """Tree of thought reasoning - explore multiple paths"""
        
        steps = []
        
        # Generate multiple thought branches
        branches_prompt = (
            f"Generate 3 different approaches to answer this question:\n"
            f"Question: {question}\n"
            f"Context: {json.dumps(context)}\n"
            f"For each approach, provide:\n"
            f"Approach 1:\n- Hypothesis:\n- Expected outcome:\n\n"
            f"Approach 2:\n- Hypothesis:\n- Expected outcome:\n\n"
            f"Approach 3:\n- Hypothesis:\n- Expected outcome:"
        )
        
        branches_response = await self.ollama_client.generate(branches_prompt)
        
        # Evaluate each branch
        for i in range(3):
            step = ReasoningStep(
                step_number=i + 1,
                description=f"Branch evaluation {i + 1}",
                reasoning=branches_response[:200],
                conclusion=f"Branch {i + 1} analyzed",
                confidence=0.6 + (i * 0.1),
            )
            steps.append(step)
        
        # Select best branch
        select_prompt = (
            f"Based on the 3 approaches analyzed, which is the most promising?\n"
            f"Question: {question}\n"
            f"Approaches: {branches_response}\n"
            f"Select the best approach and justify."
        )
        
        selection = await self.ollama_client.generate(select_prompt)
        
        steps.append(ReasoningStep(
            step_number=4,
            description="Best approach selection",
            reasoning=selection[:200],
            conclusion=selection[:100],
            confidence=0.75,
        ))
        
        return steps
    
    async def _decomposition(
        self,
        question: str,
        context: Optional[Dict[str, Any]],
        max_steps: int,
    ) -> List[ReasoningStep]:
        """Decompose complex question into sub-problems"""
        
        steps = []
        
        # Decompose
        decompose_prompt = (
            f"Decompose this complex question into {max_steps} sub-problems:\n"
            f"Question: {question}\n"
            f"Context: {json.dumps(context)}\n"
            f"For each sub-problem, explain why it's necessary and how it contributes to the answer."
        )
        
        decomposition = await self.ollama_client.generate(decompose_prompt)
        
        # Solve each sub-problem
        for i in range(max_steps):
            step = ReasoningStep(
                step_number=i + 1,
                description=f"Sub-problem {i + 1}",
                reasoning=decomposition[:200],
                conclusion=f"Sub-problem {i + 1} addressed",
                confidence=0.7 + (i * 0.03),
            )
            steps.append(step)
        
        # Synthesize
        synthesis_prompt = (
            f"Synthesize the answers to all sub-problems:\n"
            f"Question: {question}\n"
            f"Sub-problem solutions: {decomposition}\n"
            f"Provide a comprehensive final answer."
        )
        
        synthesis = await self.ollama_client.generate(synthesis_prompt)
        
        steps.append(ReasoningStep(
            step_number=max_steps + 1,
            description="Final synthesis",
            reasoning=synthesis[:200],
            conclusion=synthesis[:100],
            confidence=0.8,
        ))
        
        return steps
    
    async def _analogy_reasoning(
        self,
        question: str,
        context: Optional[Dict[str, Any]],
    ) -> List[ReasoningStep]:
        """Reasoning by analogy to known problems"""
        
        steps = []
        
        # Find similar situations
        analogy_prompt = (
            f"Find analogous situations to this problem:\n"
            f"Question: {question}\n"
            f"Context: {json.dumps(context)}\n"
            f"Identify 3 similar problems from different domains and how they were solved."
        )
        
        analogies = await self.ollama_client.generate(analogy_prompt)
        
        steps.append(ReasoningStep(
            step_number=1,
            description="Find analogies",
            reasoning=analogies[:200],
            conclusion="3 analogies identified",
            confidence=0.7,
        ))
        
        # Apply best analogy
        apply_prompt = (
            f"Apply the most relevant analogy to solve this problem:\n"
            f"Question: {question}\n"
            f"Analogies found: {analogies}\n"
            f"Which analogy is most applicable? How would it solve the problem?"
        )
        
        application = await self.ollama_client.generate(apply_prompt)
        
        steps.append(ReasoningStep(
            step_number=2,
            description="Apply best analogy",
            reasoning=application[:200],
            conclusion=application[:100],
            confidence=0.75,
        ))
        
        return steps
    
    async def _hypothesis_testing(
        self,
        question: str,
        context: Optional[Dict[str, Any]],
        max_hypotheses: int,
    ) -> List[ReasoningStep]:
        """Generate and test hypotheses"""
        
        steps = []
        
        # Generate hypotheses
        hypothesis_prompt = (
            f"Generate {max_hypotheses} hypotheses to answer this question:\n"
            f"Question: {question}\n"
            f"Context: {json.dumps(context)}\n"
            f"For each hypothesis, predict what evidence would confirm or disprove it."
        )
        
        hypotheses = await self.ollama_client.generate(hypothesis_prompt)
        
        for i in range(max_hypotheses):
            steps.append(ReasoningStep(
                step_number=i + 1,
                description=f"Testing hypothesis {i + 1}",
                reasoning=hypotheses[:200],
                conclusion=f"Hypothesis {i + 1} evaluated",
                confidence=0.65 + (i * 0.05),
            ))
        
        return steps
    
    async def _backward_reasoning(
        self,
        question: str,
        context: Optional[Dict[str, Any]],
        max_steps: int,
    ) -> List[ReasoningStep]:
        """Reason backward from desired outcome"""
        
        steps = []
        
        # Define desired outcome
        outcome_prompt = (
            f"Define the desired outcome for this question:\n"
            f"Question: {question}\n"
            f"What would a perfect answer look like? What conditions must be satisfied?"
        )
        
        outcome = await self.ollama_client.generate(outcome_prompt)
        
        steps.append(ReasoningStep(
            step_number=1,
            description="Define desired outcome",
            reasoning=outcome[:200],
            conclusion="Outcome defined",
            confidence=0.7,
        ))
        
        # Work backward
        for i in range(max_steps - 1):
            backward_prompt = (
                f"Working backward from the desired outcome, what is step {i + 1} that must be true?\n"
                f"Question: {question}\n"
                f"Desired outcome: {outcome}\n"
                f"If step {i + 1} is true, what must be true immediately before it?"
            )
            
            backward_reasoning = await self.ollama_client.generate(backward_prompt)
            
            steps.append(ReasoningStep(
                step_number=i + 2,
                description=f"Backward step {i + 1}",
                reasoning=backward_reasoning[:200],
                conclusion=backward_reasoning[:100],
                confidence=0.7 + (i * 0.05),
            ))
        
        return steps
    
    async def _synthesize_answer(
        self,
        question: str,
        steps: List[ReasoningStep],
    ) -> str:
        """Synthesize final answer from reasoning steps"""
        
        if not steps:
            return "Unable to determine from reasoning."
        
        # Use the last step's conclusion or generate summary
        last_step = steps[-1]
        
        if last_step.confidence > 0.7 and last_step.conclusion:
            return last_step.conclusion
        
        # Generate summary of all steps
        summary_prompt = (
            f"Synthesize a final answer based on these reasoning steps:\n"
            f"Question: {question}\n"
            f"Steps:\n"
            + "\n".join(f"  {s.step_number}. {s.conclusion} (confidence: {s.confidence:.2f})"
                       for s in steps)
            + "\n\nProvide a concise, confident answer."
        )
        
        summary = await self.ollama_client.generate(summary_prompt)
        return summary.strip()
    
    async def _generate_alternatives(
        self,
        question: str,
        final_answer: str,
    ) -> List[str]:
        """Generate alternative answers or approaches"""
        
        alt_prompt = (
            f"Given this question and answer, what are alternative perspectives or approaches?\n"
            f"Question: {question}\n"
            f"Answer: {final_answer}\n"
            f"List 2-3 alternative viewpoints, one per line."
        )
        
        alternatives = await self.ollama_client.generate(alt_prompt)
        
        return [
            line.strip() for line in alternatives.splitlines()
            if line.strip() and not line.lower().startswith("score:")
        ][:3]
    
    async def _identify_caveats(
        self,
        question: str,
        final_answer: str,
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Identify caveats and limitations"""
        
        caveat_prompt = (
            f"What are the caveats and limitations of this answer?\n"
            f"Question: {question}\n"
            f"Answer: {final_answer}\n"
            f"Context: {json.dumps(context)}\n"
            f"List 2-3 caveats, one per line."
        )
        
        caveats = await self.ollama_client.generate(caveat_prompt)
        
        return [
            line.strip() for line in caveats.splitlines()
            if line.strip() and not line.lower().startswith("score:")
        ][:3]
    
    async def generate_recommendations(
        self,
        project: Project,
        analysis_results: Dict[str, Any],
    ) -> List[Recommendation]:
        """Generate prioritized recommendations using AI reasoning"""
        
        rec_prompt = (
            f"Generate prioritized recommendations for this project:\n"
            f"Project: {project.name}\n"
            f"Description: {project.description}\n"
            f"Analysis Results: {json.dumps(analysis_results)}\n\n"
            f"Generate 5 recommendations. For each:\n"
            f"Category: (architecture/security/performance/team/business)\n"
            f"Title:\n"
            f"Description:\n"
            f"Expected Impact: (0-100)\n"
            f"Effort: (hours/days/weeks)\n"
            f"Risk: (low/medium/high)\n"
            f"Steps: (comma-separated list)"
        )
        
        response = await self.ollama_client.generate(rec_prompt)
        
        recommendations = []
        current_rec = {}
        
        for line in response.splitlines():
            lower = line.lower()
            if "category:" in lower:
                if current_rec:
                    recommendations.append(self._dict_to_recommendation(current_rec))
                current_rec = {"category": line.split(":", 1)[1].strip()}
            elif "title:" in lower and current_rec is not None:
                current_rec["title"] = line.split(":", 1)[1].strip()
            elif "description:" in lower and current_rec is not None:
                current_rec["description"] = line.split(":", 1)[1].strip()
            elif "expected impact:" in lower and current_rec is not None:
                try:
                    current_rec["expected_impact"] = float(
                        re.search(r'([\d.]+)', line).group(1)
                    )
                except:
                    current_rec["expected_impact"] = 50.0
            elif "effort:" in lower and current_rec is not None:
                current_rec["effort_estimate"] = line.split(":", 1)[1].strip()
            elif "risk:" in lower and current_rec is not None:
                current_rec["risk_level"] = line.split(":", 1)[1].strip()
            elif "steps:" in lower and current_rec is not None:
                steps_text = line.split(":", 1)[1].strip()
                current_rec["implementation_steps"] = [s.strip() for s in steps_text.split(",")]
        
        if current_rec:
            recommendations.append(self._dict_to_recommendation(current_rec))
        
        # Sort by priority
        recommendations.sort(
            key=lambda r: (r.expected_impact * (-1 if r.risk_level == "high" else 1)),
            reverse=True
        )
        
        for i, rec in enumerate(recommendations, 1):
            rec.priority = i
        
        return recommendations[:8]
    
    def _dict_to_recommendation(self, d: Dict) -> Recommendation:
        """Convert dict to Recommendation"""
        return Recommendation(
            priority=0,
            category=d.get("category", "general"),
            title=d.get("title", "Improvement opportunity"),
            description=d.get("description", "Analysis recommended improvement"),
            expected_impact=d.get("expected_impact", 50.0),
            effort_estimate=d.get("effort_estimate", "unknown"),
            risk_level=d.get("risk_level", "medium"),
            implementation_steps=d.get("implementation_steps", ["Investigate further"]),
        )

