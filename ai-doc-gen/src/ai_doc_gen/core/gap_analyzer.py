"""
Gap Analysis Module

Identifies documentation gaps and generates actionable reports for resolution.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .confidence_scoring import GapAnalysis, GapType

logger = logging.getLogger(__name__)

class GapReport(BaseModel):
    """Comprehensive gap analysis report."""
    timestamp: str
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int
    gaps_by_type: Dict[str, int]
    gaps_by_section: Dict[str, List[str]]
    sme_questions: List[Dict[str, str]]
    recommended_actions: List[str]
    estimated_resolution_time: str

class GapAnalyzer:
    """Analyzes documentation gaps and generates actionable reports."""

    def __init__(self, confidence_threshold: float = 70.0):
        """Initialize gap analyzer with confidence threshold."""
        self.confidence_threshold = confidence_threshold
        self.gap_history: List[GapAnalysis] = []

    def analyze_documentation_gaps(
        self,
        content: Dict[str, Any],
        confidence_scores: Dict[str, float],
        context: Optional[str] = None
    ) -> List[GapAnalysis]:
        """Analyze documentation gaps based on content and confidence scores."""
        gaps = []

        for section, confidence in confidence_scores.items():
            if confidence < self.confidence_threshold:
                gap = self._create_gap_analysis(section, confidence, content.get(section, ""), context)
                gaps.append(gap)
                self.gap_history.append(gap)

        return gaps

    def _create_gap_analysis(
        self,
        section: str,
        confidence: float,
        content: str,
        context: Optional[str]
    ) -> GapAnalysis:
        """Create a gap analysis for a specific section."""
        gap_type = self._determine_gap_type(confidence, content)
        severity = self._determine_severity(confidence)

        return GapAnalysis(
            gap_type=gap_type,
            description=f"Low confidence ({confidence}%) in section: {section}",
            confidence=confidence,
            severity=severity,
            affected_sections=[section],
            suggested_actions=self._generate_suggested_actions(gap_type, confidence, section),
            sme_questions=self._generate_sme_questions(gap_type, section, content)
        )

    def _determine_gap_type(self, confidence: float, content: str) -> GapType:
        """Determine the type of gap based on confidence and content analysis."""
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

    def _generate_suggested_actions(
        self,
        gap_type: GapType,
        confidence: float,
        section: str
    ) -> List[str]:
        """Generate suggested actions for addressing gaps."""
        actions = []

        if gap_type == GapType.MISSING_INFO:
            actions.extend([
                f"Consult with Subject Matter Expert (SME) for {section}",
                "Review source documentation and specifications",
                "Check for updated hardware specifications",
                "Validate against product datasheets"
            ])
        elif gap_type == GapType.UNCLEAR_INFO:
            actions.extend([
                f"Request clarification from technical team for {section}",
                "Review related documentation sections",
                "Validate against hardware specifications",
                "Cross-reference with installation guides"
            ])
        elif gap_type == GapType.CONFLICTING_INFO:
            actions.extend([
                "Resolve conflicts with technical team",
                "Cross-reference multiple sources",
                "Update documentation standards",
                "Establish single source of truth"
            ])
        elif gap_type == GapType.OUTDATED_INFO:
            actions.extend([
                "Update with current specifications",
                "Verify against latest hardware versions",
                "Review change management process",
                "Update version control documentation"
            ])
        elif gap_type == GapType.INCOMPLETE_INFO:
            actions.extend([
                f"Complete missing information for {section}",
                "Request additional details from SME",
                "Expand documentation coverage",
                "Add missing technical specifications"
            ])

        return actions

    def _generate_sme_questions(
        self,
        gap_type: GapType,
        section: str,
        content: str
    ) -> List[Dict[str, str]]:
        """Generate SME questions based on gap type and section."""
        questions = []

        if gap_type == GapType.MISSING_INFO:
            questions.extend([
                {
                    "question": f"What are the complete specifications for {section}?",
                    "priority": "High",
                    "category": "Technical Specifications",
                    "rationale": "Missing critical information needed for documentation"
                },
                {
                    "question": f"Are there any dependencies or prerequisites for {section}?",
                    "priority": "Medium",
                    "category": "Dependencies",
                    "rationale": "Ensure complete coverage of requirements"
                }
            ])
        elif gap_type == GapType.UNCLEAR_INFO:
            questions.extend([
                {
                    "question": f"Can you clarify the technical requirements for {section}?",
                    "priority": "High",
                    "category": "Clarification",
                    "rationale": "Current information is ambiguous and needs clarification"
                },
                {
                    "question": f"What are the best practices for implementing {section}?",
                    "priority": "Medium",
                    "category": "Best Practices",
                    "rationale": "Provide guidance for proper implementation"
                }
            ])
        elif gap_type == GapType.INCOMPLETE_INFO:
            questions.extend([
                {
                    "question": f"What additional details are needed to complete {section}?",
                    "priority": "High",
                    "category": "Completeness",
                    "rationale": "Section is incomplete and needs additional information"
                },
                {
                    "question": f"Are there any edge cases or exceptions for {section}?",
                    "priority": "Medium",
                    "category": "Edge Cases",
                    "rationale": "Ensure comprehensive coverage of all scenarios"
                }
            ])

        return questions

    def generate_gap_report(self, gaps: List[GapAnalysis]) -> GapReport:
        """Generate a comprehensive gap analysis report."""
        if not gaps:
            return GapReport(
                timestamp=datetime.now().isoformat(),
                total_gaps=0,
                critical_gaps=0,
                high_priority_gaps=0,
                medium_priority_gaps=0,
                low_priority_gaps=0,
                gaps_by_type={},
                gaps_by_section={},
                sme_questions=[],
                recommended_actions=[],
                estimated_resolution_time="0 hours"
            )

        # Count gaps by severity
        critical_gaps = len([g for g in gaps if g.severity == "Critical"])
        high_priority_gaps = len([g for g in gaps if g.severity == "High"])
        medium_priority_gaps = len([g for g in gaps if g.severity == "Medium"])
        low_priority_gaps = len([g for g in gaps if g.severity == "Low"])

        # Count gaps by type
        gaps_by_type = {}
        for gap in gaps:
            gap_type = gap.gap_type.value
            gaps_by_type[gap_type] = gaps_by_type.get(gap_type, 0) + 1

        # Group gaps by section
        gaps_by_section = {}
        for gap in gaps:
            for section in gap.affected_sections:
                if section not in gaps_by_section:
                    gaps_by_section[section] = []
                gaps_by_section[section].append(gap.description)

        # Collect all SME questions
        all_sme_questions = []
        for gap in gaps:
            all_sme_questions.extend(gap.sme_questions)

        # Collect recommended actions
        all_actions = []
        for gap in gaps:
            all_actions.extend(gap.suggested_actions)

        # Remove duplicates while preserving order
        unique_actions = list(dict.fromkeys(all_actions))

        # Estimate resolution time
        estimated_time = self._estimate_resolution_time(gaps)

        return GapReport(
            timestamp=datetime.now().isoformat(),
            total_gaps=len(gaps),
            critical_gaps=critical_gaps,
            high_priority_gaps=high_priority_gaps,
            medium_priority_gaps=medium_priority_gaps,
            low_priority_gaps=low_priority_gaps,
            gaps_by_type=gaps_by_type,
            gaps_by_section=gaps_by_section,
            sme_questions=all_sme_questions,
            recommended_actions=unique_actions,
            estimated_resolution_time=estimated_time
        )

    def _estimate_resolution_time(self, gaps: List[GapAnalysis]) -> str:
        """Estimate time needed to resolve all gaps."""
        total_hours = 0

        for gap in gaps:
            if gap.severity == "Critical":
                total_hours += 4  # 4 hours per critical gap
            elif gap.severity == "High":
                total_hours += 2  # 2 hours per high priority gap
            elif gap.severity == "Medium":
                total_hours += 1  # 1 hour per medium priority gap
            else:
                total_hours += 0.5  # 30 minutes per low priority gap

        if total_hours < 1:
            return f"{int(total_hours * 60)} minutes"
        elif total_hours < 8:
            return f"{total_hours:.1f} hours"
        else:
            days = total_hours / 8
            return f"{days:.1f} days"

    def prioritize_gaps(self, gaps: List[GapAnalysis]) -> List[GapAnalysis]:
        """Prioritize gaps based on severity and impact."""
        # Define priority weights
        severity_weights = {
            "Critical": 4,
            "High": 3,
            "Medium": 2,
            "Low": 1
        }

        # Calculate priority scores
        for gap in gaps:
            base_score = severity_weights.get(gap.severity, 1)
            confidence_factor = (100 - gap.confidence) / 100  # Higher confidence = lower priority
            gap.priority_score = base_score * confidence_factor

        # Sort by priority score (highest first)
        return sorted(gaps, key=lambda x: getattr(x, 'priority_score', 0), reverse=True)

    def save_gap_report(self, report: GapReport, filepath: str) -> None:
        """Save gap report to file."""
        with open(filepath, 'w') as f:
            json.dump(report.dict(), f, indent=2)

        logger.info(f"Gap report saved to {filepath}")

    def load_gap_report(self, filepath: str) -> GapReport:
        """Load gap report from file."""
        with open(filepath) as f:
            data = json.load(f)

        return GapReport(**data)

    def get_gap_trends(self) -> Dict[str, Any]:
        """Analyze gap trends over time."""
        if len(self.gap_history) < 2:
            return {"message": "Insufficient data for trend analysis"}

        # Group gaps by date
        gaps_by_date = {}
        for gap in self.gap_history:
            date = gap.timestamp.split('T')[0]  # Extract date part
            if date not in gaps_by_date:
                gaps_by_date[date] = []
            gaps_by_date[date].append(gap)

        # Calculate trends
        dates = sorted(gaps_by_date.keys())
        gap_counts = [len(gaps_by_date[date]) for date in dates]

        # Calculate average confidence over time
        confidence_trends = []
        for date in dates:
            confidences = [gap.confidence for gap in gaps_by_date[date]]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            confidence_trends.append(avg_confidence)

        return {
            "dates": dates,
            "gap_counts": gap_counts,
            "confidence_trends": confidence_trends,
            "total_gaps_analyzed": len(self.gap_history),
            "trend_period": f"{dates[0]} to {dates[-1]}" if dates else "No data"
        }
