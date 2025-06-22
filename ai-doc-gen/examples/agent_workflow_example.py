#!/usr/bin/env python3
"""
Agent Workflow Example

Demonstrates the full AI agent workflow including:
- Input processing and validation
- Managing agent for gap detection and SME questions
- Review agent for provenance and confidence audit
- LLM integration for enhanced analysis
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_doc_gen.agents import ManagingAgent, ReviewAgent
from ai_doc_gen.core.llm_integration import LLMClient
from ai_doc_gen.input_processing import (
    extract_structured_content,
    parse_document,
    validate_document,
)


def create_sample_document():
    """Create a sample document for testing."""
    sample_text = """
# Cisco Router Installation Guide

## Technical Specifications

The Cisco Router Model XYZ-1000 has the following specifications:
- Dimensions: 300mm x 200mm x 50mm
- Weight: 2.5kg
- Power: 100-240V AC, 50-60Hz
- Memory: 1GB RAM, 4GB Flash
- Ports: 4x Gigabit Ethernet, 1x Console, 1x USB

## Installation Requirements

Before installing the router, ensure you have:
- Minimum 2U rack space
- Power outlet (100-240V AC)
- Network cables (Cat5e or better)
- Console cable for initial configuration

## Installation Procedure

### Step 1: Physical Installation
1. Mount the router in a 19-inch rack using the provided mounting brackets
2. Ensure proper ventilation (minimum 2 inches clearance on all sides)
3. Connect the power cable to the router and power outlet

### Step 2: Network Connections
1. Connect network cables to the appropriate Ethernet ports
2. Connect the console cable to your computer for initial setup
3. Power on the router

### Step 3: Initial Configuration
1. Open a terminal emulator on your computer
2. Set the connection to 9600 baud, 8 data bits, no parity, 1 stop bit
3. Press Enter to access the router console

## Warnings and Notes

WARNING: Do not connect power while the router is open or being serviced.
WARNING: Ensure proper grounding to prevent electrical damage.

Note: The router may take up to 5 minutes to fully boot after power-on.
Note: Keep the original packaging for warranty purposes.

## Troubleshooting

### Common Issues
- Router won't power on: Check power cable and outlet
- No network connectivity: Verify cable connections and network settings
- Console access issues: Check terminal emulator settings

### Error Messages
- "Boot failed": Contact technical support
- "Memory error": Check memory module installation
"""

    # Write sample text file
    sample_file = "sample_router_guide.txt"
    with open(sample_file, "w") as f:
        f.write(sample_text)

    print(f"Created sample document: {sample_file}")
    return sample_file


async def demonstrate_agent_workflow():
    """Demonstrate the full agent workflow."""
    print("\n" + "="*80)
    print("AI AGENT WORKFLOW DEMONSTRATION")
    print("="*80)

    # Step 1: Create and validate sample document
    print("\nStep 1: Document Validation")
    print("-" * 40)

    sample_file = create_sample_document()

    try:
        validation_result = validate_document(sample_file)
        print(f"Document valid: {validation_result.is_valid}")
        print(f"Validation score: {validation_result.score:.2f}")

        if not validation_result.is_valid:
            print("Document validation failed!")
            for warning in validation_result.warnings:
                print(f"  Warning: {warning}")
            return

        # Step 2: Parse and extract structured content
        print("\nStep 2: Content Extraction")
        print("-" * 40)

        parsed_doc = parse_document(sample_file)
        print(f"Parsed document: {parsed_doc.filename}")
        print(f"Sections found: {len(parsed_doc.sections)}")

        extracted_content = extract_structured_content(parsed_doc)
        print(f"Extracted content items: {len(extracted_content)}")

        # Show some extracted content
        for i, item in enumerate(extracted_content[:3], 1):
            print(f"\n{i}. {item.title}")
            print(f"   Type: {item.content_type.value}")
            print(f"   Confidence: {item.confidence:.2f}")
            print(f"   Content: {item.content[:100]}{'...' if len(item.content) > 100 else ''}")

        # Step 3: Run Managing Agent
        print("\nStep 3: Managing Agent Analysis")
        print("-" * 40)

        managing_agent = ManagingAgent()
        managing_results = managing_agent.run(extracted_content)

        print(f"Total content items: {managing_results['total_content_items']}")
        print(f"Gaps detected: {managing_results['total_gaps']}")
        print(f"SME questions generated: {managing_results['total_sme_questions']}")

        # Show confidence scores
        print("\nConfidence Scores:")
        for title, score in list(managing_results['confidence_scores'].items())[:5]:
            print(f"  {title}: {score:.1f}%")

        # Show gaps
        if managing_results['gaps']:
            print("\nDetected Gaps:")
            for gap in managing_results['gaps'][:3]:
                print(f"  - {gap.description}")
                print(f"    Severity: {gap.severity}, Confidence: {gap.confidence:.1f}%")

        # Show SME questions
        if managing_results['sme_questions']:
            print("\nSME Questions:")
            for i, question in enumerate(managing_results['sme_questions'][:3], 1):
                print(f"  {i}. {question['question']}")
                print(f"     Section: {question['section']}, Severity: {question['severity']}")

        # Step 4: Run Review Agent
        print("\nStep 4: Review Agent Audit")
        print("-" * 40)

        review_agent = ReviewAgent()

        # Create a simple provenance map
        provenance_map = {
            item.title: f"{parsed_doc.filename}#{item.source_section}"
            for item in extracted_content
        }

        review_results = review_agent.run(extracted_content, provenance_map=provenance_map)

        print(f"Total items audited: {review_results['total_items']}")
        print(f"Missing provenance: {review_results['total_missing_provenance']}")
        print(f"Low confidence items: {review_results['total_low_confidence']}")

        # Show audit results
        print("\nAudit Results:")
        for audit in review_results['audit_results'][:3]:
            print(f"  {audit['title']}")
            print(f"    Confidence: {audit['confidence']:.1f}% ({audit['confidence_level']})")
            print(f"    Provenance: {'✓' if audit['has_provenance'] else '✗'}")

        # Step 5: LLM Integration (if API key available)
        print("\nStep 5: LLM Integration")
        print("-" * 40)

        if os.getenv("OPENAI_API_KEY"):
            try:
                llm_client = LLMClient(provider="openai")

                # Generate enhanced SME questions using LLM
                if managing_results['gaps']:
                    gap_data = {
                        "gaps": [
                            {
                                "description": gap.description,
                                "severity": gap.severity,
                                "confidence": gap.confidence
                            }
                            for gap in managing_results['gaps'][:2]  # Limit to 2 for demo
                        ]
                    }

                    enhanced_questions = await llm_client.generate_sme_questions(
                        gap_data,
                        context="Cisco router installation documentation"
                    )

                    print(f"LLM-generated SME questions: {len(enhanced_questions)}")
                    for i, question in enumerate(enhanced_questions[:2], 1):
                        print(f"  {i}. {question.get('question', 'N/A')}")
                        print(f"     Priority: {question.get('priority', 'N/A')}")

            except Exception as e:
                print(f"LLM integration error: {e}")
                print("(This is expected if no API key is configured)")
        else:
            print("No OpenAI API key found in environment")
            print("Set OPENAI_API_KEY in your .env file to enable LLM features")

        # Step 6: Generate final report
        print("\nStep 6: Final Report")
        print("-" * 40)

        final_report = {
            "document_info": {
                "filename": parsed_doc.filename,
                "title": parsed_doc.title,
                "sections": len(parsed_doc.sections),
                "validation_score": validation_result.score
            },
            "extraction_summary": {
                "total_items": len(extracted_content),
                "content_types": {},
                "average_confidence": sum(item.confidence for item in extracted_content) / len(extracted_content) * 100
            },
            "managing_agent_results": {
                "gaps_detected": len(managing_results['gaps']),
                "sme_questions": len(managing_results['sme_questions']),
                "average_confidence": sum(managing_results['confidence_scores'].values()) / len(managing_results['confidence_scores'])
            },
            "review_agent_results": {
                "items_audited": review_results['total_items'],
                "missing_provenance": review_results['total_missing_provenance'],
                "low_confidence_items": review_results['total_low_confidence']
            },
            "recommendations": [
                "Review and address high-severity gaps",
                "Obtain SME clarifications for low-confidence items",
                "Ensure all content has proper provenance tracking"
            ]
        }

        # Count content types
        for item in extracted_content:
            content_type = item.content_type.value
            final_report["extraction_summary"]["content_types"][content_type] = \
                final_report["extraction_summary"]["content_types"].get(content_type, 0) + 1

        print("Final Report Generated:")
        print(json.dumps(final_report, indent=2))

        # Save report
        report_file = "agent_workflow_report.json"
        with open(report_file, "w") as f:
            json.dump(final_report, f, indent=2)
        print(f"\nReport saved to: {report_file}")

    except Exception as e:
        print(f"Error in workflow demonstration: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if os.path.exists(sample_file):
            os.remove(sample_file)


async def main():
    """Main demonstration function."""
    print("AI DOCUMENTATION GENERATION - AGENT WORKFLOW DEMONSTRATION")
    print("="*80)

    await demonstrate_agent_workflow()

    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the agent_workflow_report.json file")
    print("2. Configure OpenAI API key in .env for LLM features")
    print("3. Integrate agents into the full pipeline")
    print("4. Add more sophisticated gap analysis and SME question generation")


if __name__ == "__main__":
    asyncio.run(main())
