"""
Managing Agent for documentation workflow orchestration.
"""

from typing import Any, Dict, List

from ai_doc_gen.core.confidence_scoring import ConfidenceScorer, GapAnalysis
from ai_doc_gen.input_processing.structured_extractor import ExtractedContent

from .base import AgentBase


class ManagingAgent(AgentBase):
    """Agent for managing documentation workflow, gap detection, and SME queries."""
    def __init__(self, name: str = "ManagingAgent", confidence_threshold: float = 85.0):
        super().__init__(name)
        self.confidence_scorer = ConfidenceScorer(default_threshold=confidence_threshold)
        self.last_run_results: Dict[str, Any] = {}

    def run(self, extracted_content: List[ExtractedContent], **kwargs) -> Dict[str, Any]:
        """Orchestrate workflow: detect gaps, generate SME questions, prepare for draft generation."""
        # Step 1: Score confidence for each content item
        confidence_scores = {item.title: item.confidence * 100 for item in extracted_content}

        # Step 2: Analyze gaps
        content_dict = {item.title: item.content for item in extracted_content}
        gaps = self.confidence_scorer.analyze_gaps(content_dict, confidence_scores)

        # Step 3: Generate SME questions for low-confidence gaps
        sme_questions = self._generate_sme_questions(gaps)

        # Step 4: Prepare results
        results = {
            "confidence_scores": confidence_scores,
            "gaps": gaps,
            "sme_questions": sme_questions,
            "total_content_items": len(extracted_content),
            "total_gaps": len(gaps),
            "total_sme_questions": len(sme_questions)
        }
        self.last_run_results = results
        return results

    def _generate_sme_questions(self, gaps: List[GapAnalysis]) -> List[Dict[str, str]]:
        """Generate SME questions for each gap."""
        questions = []
        for gap in gaps:
            question = {
                "section": gap.affected_sections[0] if gap.affected_sections else "Unknown",
                "question": f"Can you clarify or provide more detail for: {gap.description}?",
                "severity": gap.severity,
                "gap_type": gap.gap_type.value
            }
            questions.append(question)
        return questions

    def report(self) -> Dict[str, Any]:
        """Return a summary of the last run."""
        return self.last_run_results or {"message": "No run has been performed yet."}
