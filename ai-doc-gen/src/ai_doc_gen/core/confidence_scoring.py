"""
Enhanced Confidence Scoring System

Based on the original test_confidence_scoring.py but enhanced for:
- Multi-agent confidence aggregation
- Gap analysis confidence scoring
- Provenance confidence tracking
- Advanced threshold management
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence level enumeration."""
    VERY_LOW = (0, 29)
    LOW = (30, 49)
    MEDIUM = (50, 69)
    HIGH = (70, 89)
    VERY_HIGH = (90, 100)
    NOT_FOUND = (100, 100)

class GapType(Enum):
    """Types of documentation gaps."""
    MISSING_INFO = "missing_info"
    UNCLEAR_INFO = "unclear_info"
    CONFLICTING_INFO = "conflicting_info"
    OUTDATED_INFO = "outdated_info"
    INCOMPLETE_INFO = "incomplete_info"

@dataclass
class ConfidenceScore:
    """Individual confidence score with metadata."""
    value: float
    source: str
    timestamp: str
    context: Optional[str] = None
    gap_type: Optional[GapType] = None

class GapAnalysis(BaseModel):
    """Gap analysis result with confidence scoring."""
    gap_type: GapType
    description: str
    confidence: float = Field(ge=0, le=100)
    severity: str = Field(pattern="^(Critical|High|Medium|Low)$")
    affected_sections: List[str] = []
    suggested_actions: List[str] = []
    sme_questions: List[Dict[str, str]] = []

class ConfidenceScorer:
    """Enhanced confidence scoring system for multi-agent architecture."""

    def __init__(self, default_threshold: float = 85.0):
        """Initialize confidence scorer with default threshold."""
        self.default_threshold = default_threshold
        self.confidence_history: List[ConfidenceScore] = []

    def validate_confidence_score(self, score: float) -> bool:
        """Validate that confidence score is within valid range."""
        return 0 <= score <= 100

    def get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Get confidence level enum for a given score."""
        for level in ConfidenceLevel:
            min_score, max_score = level.value
            if min_score <= score <= max_score:
                return level
        return ConfidenceLevel.VERY_LOW

    def calculate_average_confidence(self, scores: List[float]) -> float:
        """Calculate average confidence from a list of scores."""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def apply_threshold_triage(
        self,
        items: List[Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Apply threshold-based triage to items with confidence scores."""
        if threshold is None:
            threshold = self.default_threshold

        auto_approved = []
        review_needed = []

        for item in items:
            confidence = item.get('confidence', 100)

            if confidence >= threshold:
                auto_approved.append(item)
            else:
                review_needed.append(item)

        return {
            "threshold": threshold,
            "total_items": len(items),
            "auto_approved": len(auto_approved),
            "review_needed": len(review_needed),
            "approved": auto_approved,
            "review": review_needed,
            "approval_rate": (len(auto_approved) / len(items) * 100) if items else 0,
            "average_confidence": self.calculate_average_confidence(
                [item.get('confidence', 100) for item in items]
            )
        }

    def aggregate_agent_confidence(
        self,
        agent_scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Aggregate confidence scores from multiple agents with optional weights."""
        if not agent_scores:
            return 0.0

        if weights is None:
            # Equal weights if not specified
            weights = {agent: 1.0 / len(agent_scores) for agent in agent_scores}

        # Normalize weights
        total_weight = sum(weights.values())
        normalized_weights = {agent: weight / total_weight for agent, weight in weights.items()}

        # Calculate weighted average
        weighted_sum = sum(
            agent_scores[agent] * normalized_weights[agent]
            for agent in agent_scores
            if agent in normalized_weights
        )

        return weighted_sum

    def analyze_gaps(
        self,
        content: Dict[str, Any],
        confidence_scores: Dict[str, float]
    ) -> List[GapAnalysis]:
        """Analyze documentation gaps based on confidence scores."""
        gaps = []

        for section, confidence in confidence_scores.items():
            if confidence < 70:  # Threshold for gap analysis
                gap_type = self._determine_gap_type(confidence, content.get(section, ""))
                severity = self._determine_severity(confidence)

                gap = GapAnalysis(
                    gap_type=gap_type,
                    description=f"Low confidence ({confidence}%) in section: {section}",
                    confidence=confidence,
                    severity=severity,
                    affected_sections=[section],
                    suggested_actions=self._generate_suggested_actions(gap_type, confidence)
                )
                gaps.append(gap)

        return gaps

    def _determine_gap_type(self, confidence: float, content: str) -> GapType:
        """Determine the type of gap based on confidence and content."""
        if confidence < 30:
            return GapType.MISSING_INFO
        elif confidence < 50:
            return GapType.UNCLEAR_INFO
        elif confidence < 70:
            return GapType.INCOMPLETE_INFO
        else:
            return GapType.UNCLEAR_INFO

    def _determine_severity(self, confidence: float) -> str:
        """Determine severity based on confidence score."""
        if confidence < 30:
            return "Critical"
        elif confidence < 50:
            return "High"
        elif confidence < 70:
            return "Medium"
        else:
            return "Low"

    def _generate_suggested_actions(self, gap_type: GapType, confidence: float) -> List[str]:
        """Generate suggested actions for addressing gaps."""
        actions = []

        if gap_type == GapType.MISSING_INFO:
            actions.extend([
                "Consult with Subject Matter Expert (SME)",
                "Review source documentation",
                "Check for updated specifications"
            ])
        elif gap_type == GapType.UNCLEAR_INFO:
            actions.extend([
                "Request clarification from technical team",
                "Review related documentation sections",
                "Validate against hardware specifications"
            ])
        elif gap_type == GapType.CONFLICTING_INFO:
            actions.extend([
                "Resolve conflicts with technical team",
                "Cross-reference multiple sources",
                "Update documentation standards"
            ])
        elif gap_type == GapType.OUTDATED_INFO:
            actions.extend([
                "Update with current specifications",
                "Verify against latest hardware versions",
                "Review change management process"
            ])
        elif gap_type == GapType.INCOMPLETE_INFO:
            actions.extend([
                "Complete missing information",
                "Request additional details from SME",
                "Expand documentation coverage"
            ])

        return actions

    def track_provenance_confidence(
        self,
        source: str,
        confidence: float,
        context: Optional[str] = None
    ) -> None:
        """Track confidence scores for provenance analysis."""
        score = ConfidenceScore(
            value=confidence,
            source=source,
            timestamp=self._get_timestamp(),
            context=context
        )
        self.confidence_history.append(score)

    def get_provenance_report(self) -> Dict[str, Any]:
        """Generate provenance confidence report."""
        if not self.confidence_history:
            return {"message": "No confidence history available"}

        sources = {}
        for score in self.confidence_history:
            if score.source not in sources:
                sources[score.source] = []
            sources[score.source].append(score.value)

        report = {
            "total_entries": len(self.confidence_history),
            "sources": {},
            "overall_average": self.calculate_average_confidence(
                [score.value for score in self.confidence_history]
            )
        }

        for source, scores in sources.items():
            report["sources"][source] = {
                "count": len(scores),
                "average": self.calculate_average_confidence(scores),
                "min": min(scores),
                "max": max(scores)
            }

        return report

    def _get_timestamp(self) -> str:
        """Get current timestamp for tracking."""
        from datetime import datetime
        return datetime.now().isoformat()

    def save_confidence_data(self, filepath: str, data: Dict[str, Any]) -> None:
        """Save confidence data to file with enhanced metadata."""
        output_data = {
            "metadata": {
                "timestamp": self._get_timestamp(),
                "threshold": self.default_threshold,
                "version": "2.0"
            },
            "data": data
        }

        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Confidence data saved to {filepath}")

    def load_confidence_data(self, filepath: str) -> Dict[str, Any]:
        """Load confidence data from file."""
        with open(filepath) as f:
            data = json.load(f)

        # Handle both old and new format
        if "metadata" in data:
            return data["data"]
        else:
            return data

# Convenience functions for backward compatibility
def validate_confidence_scores(specs: List[Dict[str, Any]], threshold: float = 85.0) -> Tuple[List[Dict], List[Dict]]:
    """Backward compatibility function for confidence validation."""
    scorer = ConfidenceScorer(threshold)
    triage_result = scorer.apply_threshold_triage(specs, threshold)
    return triage_result["approved"], triage_result["review"]

def calculate_average_confidence(scores: List[float]) -> float:
    """Backward compatibility function for average confidence calculation."""
    scorer = ConfidenceScorer()
    return scorer.calculate_average_confidence(scores)
