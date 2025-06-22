"""
Review Agent for provenance and confidence audit.
"""

from typing import Any, Dict, List, Optional

from ai_doc_gen.core.confidence_scoring import ConfidenceScorer
from ai_doc_gen.input_processing.structured_extractor import ExtractedContent

from .base import AgentBase


class ReviewAgent(AgentBase):
    """Agent for auditing provenance and confidence in documentation."""
    def __init__(self, name: str = "ReviewAgent"):
        super().__init__(name)
        self.confidence_scorer = ConfidenceScorer()
        self.last_audit: Dict[str, Any] = {}

    def run(self, extracted_content: List[ExtractedContent], provenance_map: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Audit provenance and confidence for extracted content."""
        audit_results = []
        missing_provenance = []
        low_confidence = []
        for item in extracted_content:
            provenance = None
            if provenance_map:
                provenance = provenance_map.get(item.title)
            audit_entry = {
                "title": item.title,
                "confidence": item.confidence * 100,
                "provenance": provenance or "Unknown",
                "has_provenance": provenance is not None,
                "confidence_level": self.confidence_scorer.get_confidence_level(item.confidence * 100).name
            }
            audit_results.append(audit_entry)
            if not provenance:
                missing_provenance.append(item.title)
            if item.confidence * 100 < 85:
                low_confidence.append(item.title)
        summary = {
            "audit_results": audit_results,
            "missing_provenance": missing_provenance,
            "low_confidence": low_confidence,
            "total_items": len(extracted_content),
            "total_missing_provenance": len(missing_provenance),
            "total_low_confidence": len(low_confidence)
        }
        self.last_audit = summary
        return summary

    def report(self) -> Dict[str, Any]:
        """Return a summary of the last audit."""
        return self.last_audit or {"message": "No audit has been performed yet."}
