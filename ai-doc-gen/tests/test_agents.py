"""
Tests for AI agents (ManagingAgent and ReviewAgent).
"""

from unittest.mock import Mock

import pytest

from ai_doc_gen.agents import ManagingAgent, ReviewAgent
from ai_doc_gen.input_processing.structured_extractor import (
    ContentType,
    ExtractedContent,
)


class TestManagingAgent:
    """Test ManagingAgent functionality."""

    def test_managing_agent_initialization(self):
        """Test ManagingAgent initialization."""
        agent = ManagingAgent()
        assert agent.name == "ManagingAgent"
        assert agent.confidence_scorer is not None

    def test_managing_agent_custom_name(self):
        """Test ManagingAgent with custom name."""
        agent = ManagingAgent(name="CustomAgent")
        assert agent.name == "CustomAgent"

    def test_managing_agent_run_with_content(self):
        """Test ManagingAgent run method with extracted content."""
        agent = ManagingAgent()

        # Create mock extracted content
        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Spec 1",
                content="Test specification content",
                confidence=0.8,
                source_section="Section 1"
            ),
            ExtractedContent(
                content_type=ContentType.INSTALLATION_PROCEDURE,
                title="Install 1",
                content="Test installation content",
                confidence=0.6,
                source_section="Section 2"
            )
        ]

        results = agent.run(content_items)

        assert "confidence_scores" in results
        assert "gaps" in results
        assert "sme_questions" in results
        assert results["total_content_items"] == 2
        assert len(results["confidence_scores"]) == 2

    def test_managing_agent_generate_sme_questions(self):
        """Test SME question generation."""
        agent = ManagingAgent()

        # Mock gap analysis
        gaps = [
            Mock(
                description="Missing technical details",
                affected_sections=["Section 1"],
                severity="High",
                gap_type=Mock(value="missing_info")
            )
        ]

        questions = agent._generate_sme_questions(gaps)

        assert len(questions) == 1
        assert "section" in questions[0]
        assert "question" in questions[0]
        assert "severity" in questions[0]
        assert "gap_type" in questions[0]

    def test_managing_agent_report(self):
        """Test ManagingAgent report method."""
        agent = ManagingAgent()

        # Test report before running
        report = agent.report()
        assert "message" in report

        # Test report after running
        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Test",
                content="Test content",
                confidence=0.8,
                source_section="Test Section"
            )
        ]

        agent.run(content_items)
        report = agent.report()
        assert "confidence_scores" in report


class TestReviewAgent:
    """Test ReviewAgent functionality."""

    def test_review_agent_initialization(self):
        """Test ReviewAgent initialization."""
        agent = ReviewAgent()
        assert agent.name == "ReviewAgent"
        assert agent.confidence_scorer is not None

    def test_review_agent_custom_name(self):
        """Test ReviewAgent with custom name."""
        agent = ReviewAgent(name="CustomReviewAgent")
        assert agent.name == "CustomReviewAgent"

    def test_review_agent_run_with_content(self):
        """Test ReviewAgent run method with extracted content."""
        agent = ReviewAgent()

        # Create mock extracted content
        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Spec 1",
                content="Test specification content",
                confidence=0.9,
                source_section="Section 1"
            ),
            ExtractedContent(
                content_type=ContentType.INSTALLATION_PROCEDURE,
                title="Install 1",
                content="Test installation content",
                confidence=0.7,
                source_section="Section 2"
            )
        ]

        results = agent.run(content_items)

        assert "audit_results" in results
        assert "missing_provenance" in results
        assert "low_confidence" in results
        assert results["total_items"] == 2
        assert len(results["audit_results"]) == 2

    def test_review_agent_run_with_provenance(self):
        """Test ReviewAgent run method with provenance mapping."""
        agent = ReviewAgent()

        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Spec 1",
                content="Test content",
                confidence=0.8,
                source_section="Section 1"
            )
        ]

        provenance_map = {"Spec 1": "source_document.pdf"}

        results = agent.run(content_items, provenance_map=provenance_map)

        assert results["total_missing_provenance"] == 0
        assert len(results["audit_results"]) == 1
        assert results["audit_results"][0]["has_provenance"] is True

    def test_review_agent_run_without_provenance(self):
        """Test ReviewAgent run method without provenance mapping."""
        agent = ReviewAgent()

        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Spec 1",
                content="Test content",
                confidence=0.8,
                source_section="Section 1"
            )
        ]

        results = agent.run(content_items)

        assert results["total_missing_provenance"] == 1
        assert len(results["audit_results"]) == 1
        assert results["audit_results"][0]["has_provenance"] is False

    def test_review_agent_low_confidence_detection(self):
        """Test ReviewAgent detection of low confidence items."""
        agent = ReviewAgent()

        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Low Confidence Spec",
                content="Test content",
                confidence=0.7,  # Below 85% threshold
                source_section="Section 1"
            ),
            ExtractedContent(
                content_type=ContentType.INSTALLATION_PROCEDURE,
                title="High Confidence Install",
                content="Test content",
                confidence=0.9,  # Above 85% threshold
                source_section="Section 2"
            )
        ]

        results = agent.run(content_items)

        assert results["total_low_confidence"] == 1
        assert "Low Confidence Spec" in results["low_confidence"]
        assert "High Confidence Install" not in results["low_confidence"]

    def test_review_agent_report(self):
        """Test ReviewAgent report method."""
        agent = ReviewAgent()

        # Test report before running
        report = agent.report()
        assert "message" in report

        # Test report after running
        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Test",
                content="Test content",
                confidence=0.8,
                source_section="Test Section"
            )
        ]

        agent.run(content_items)
        report = agent.report()
        assert "audit_results" in report


class TestAgentIntegration:
    """Integration tests for agents working together."""

    def test_agents_workflow(self):
        """Test basic workflow between ManagingAgent and ReviewAgent."""
        managing_agent = ManagingAgent()
        review_agent = ReviewAgent()

        # Create test content
        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Technical Specification",
                content="Device dimensions: 100mm x 200mm",
                confidence=0.8,
                source_section="Specifications"
            ),
            ExtractedContent(
                content_type=ContentType.INSTALLATION_PROCEDURE,
                title="Installation Steps",
                content="Step 1: Mount the device",
                confidence=0.6,
                source_section="Installation"
            )
        ]

        # Run managing agent
        managing_results = managing_agent.run(content_items)

        # Run review agent
        review_results = review_agent.run(content_items)

        # Verify both agents produced results
        assert managing_results["total_content_items"] == 2
        assert review_results["total_items"] == 2

        # Verify gap detection worked
        assert "gaps" in managing_results
        assert len(managing_results["gaps"]) > 0

        # Verify audit worked
        assert "audit_results" in review_results
        assert len(review_results["audit_results"]) == 2

    def test_agent_reports(self):
        """Test that both agents can generate reports."""
        managing_agent = ManagingAgent()
        review_agent = ReviewAgent()

        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Test",
                content="Test content",
                confidence=0.8,
                source_section="Test Section"
            )
        ]

        # Run both agents
        managing_agent.run(content_items)
        review_agent.run(content_items)

        # Get reports
        managing_report = managing_agent.report()
        review_report = review_agent.report()

        # Verify reports contain expected data
        assert "confidence_scores" in managing_report
        assert "audit_results" in review_report


if __name__ == "__main__":
    pytest.main([__file__])
