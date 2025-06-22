#!/usr/bin/env python3
"""
Basic Usage Example for AI Documentation Generation

This example demonstrates the core functionality of the AI-assisted
documentation generation system.
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main example function."""

    # Import core components
    from ai_doc_gen.core.confidence_scoring import ConfidenceScorer
    from ai_doc_gen.core.gap_analyzer import GapAnalyzer
    from ai_doc_gen.core.llm_integration import LLMClient
    from ai_doc_gen.core.pipeline_orchestrator import PipelineOrchestrator
    from ai_doc_gen.core.provenance_tracker import ProvenanceTracker

    logger.info("🚀 Starting AI Documentation Generation Example")

    # Example 1: Basic LLM Integration
    logger.info("\n📋 Example 1: LLM Integration")

    llm_client = LLMClient(provider="openai")

    # Mock content for demonstration
    sample_content = """
    The Cisco Nexus 9364C-H1 switch (N9K-C9364C-H1) is a 2-rack unit (RU), 
    fixed-port switch designed for spine-leaf-APIC deployment in data centers. 
    The software on this switch has 6.4T traffic-processing capability.
    """

    extraction_schema = {
        "specifications": [
            "Product name",
            "Model number",
            "Rack units",
            "Traffic processing capability"
        ]
    }

    try:
        result = await llm_client.extract_structured_data(
            content=sample_content,
            extraction_schema=extraction_schema
        )
        logger.info(f"✅ Extracted data: {result['data']}")
    except Exception as e:
        logger.warning(f"⚠️ LLM call failed (expected without API key): {e}")

    # Example 2: Confidence Scoring
    logger.info("\n📊 Example 2: Confidence Scoring")

    confidence_scorer = ConfidenceScorer(default_threshold=85.0)

    # Sample confidence scores
    sample_specs = [
        {"spec_item": "Product name", "value": "Cisco Nexus 9364C-H1", "confidence": 95},
        {"spec_item": "Model number", "value": "N9K-C9364C-H1", "confidence": 98},
        {"spec_item": "Rack units", "value": "2 RU", "confidence": 92},
        {"spec_item": "Missing spec", "value": "", "confidence": 45}
    ]

    triage_result = confidence_scorer.apply_threshold_triage(sample_specs, threshold=85.0)

    logger.info("✅ Confidence triage results:")
    logger.info(f"   - Total specs: {triage_result['total_items']}")
    logger.info(f"   - Auto-approved: {triage_result['auto_approved']}")
    logger.info(f"   - Review needed: {triage_result['review_needed']}")
    logger.info(f"   - Average confidence: {triage_result['average_confidence']:.1f}%")

    # Example 3: Gap Analysis
    logger.info("\n🔍 Example 3: Gap Analysis")

    gap_analyzer = GapAnalyzer(confidence_threshold=70.0)

    # Sample content and confidence scores
    content = {
        "overview": "Hardware installation guide content...",
        "specifications": "Technical specifications...",
        "installation": "Installation procedures..."
    }

    confidence_scores = {
        "overview": 85.0,
        "specifications": 45.0,  # Low confidence - will trigger gap analysis
        "installation": 92.0
    }

    gaps = gap_analyzer.analyze_documentation_gaps(content, confidence_scores)

    logger.info("✅ Gap analysis results:")
    logger.info(f"   - Total gaps identified: {len(gaps)}")

    for gap in gaps:
        logger.info(f"   - {gap.gap_type.value}: {gap.description} (Severity: {gap.severity})")

    # Generate gap report
    gap_report = gap_analyzer.generate_gap_report(gaps)
    logger.info(f"   - Estimated resolution time: {gap_report.estimated_resolution_time}")

    # Example 4: Provenance Tracking
    logger.info("\n🔗 Example 4: Provenance Tracking")

    provenance_tracker = ProvenanceTracker()

    # Add some provenance entries
    provenance_tracker.add_provenance_entry(
        item_id="product_name",
        item_type="specification",
        value="Cisco Nexus 9364C-H1",
        source_document="hardware_guide.pdf",
        source_section="overview",
        confidence=95.0,
        agent="managing_agent"
    )

    provenance_tracker.add_provenance_entry(
        item_id="model_number",
        item_type="specification",
        value="N9K-C9364C-H1",
        source_document="hardware_guide.pdf",
        source_section="overview",
        confidence=98.0,
        agent="managing_agent"
    )

    # Get provenance report
    provenance_report = provenance_tracker.get_provenance_report()

    logger.info("✅ Provenance tracking results:")
    logger.info(f"   - Total items tracked: {provenance_report['summary']['total_items']}")
    logger.info(f"   - Average confidence: {provenance_report['summary']['average_confidence']}")
    logger.info(f"   - Source documents: {provenance_report['summary']['source_documents']}")

    # Example 5: Pipeline Orchestrator
    logger.info("\n⚙️ Example 5: Pipeline Orchestrator")

    config = {
        "llm_provider": "openai",
        "confidence_threshold": 85.0,
        "gap_threshold": 70.0
    }

    orchestrator = PipelineOrchestrator(config)

    logger.info(f"✅ Pipeline initialized with {len(orchestrator.steps)} steps:")
    for i, step in enumerate(orchestrator.steps, 1):
        logger.info(f"   {i}. {step.name}")

    # Get pipeline status
    status = orchestrator.get_pipeline_status()
    logger.info(f"   - Pipeline status: {status['current_step']}/{status['total_steps']} steps")

    logger.info("\n🎉 Example completed successfully!")
    logger.info("\n📝 Next steps:")
    logger.info("   1. Set up your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    logger.info("   2. Run the full pipeline with real documents")
    logger.info("   3. Explore the generated outputs and reports")
    logger.info("   4. Customize the configuration for your specific needs")

if __name__ == "__main__":
    asyncio.run(main())
