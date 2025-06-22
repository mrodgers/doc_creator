#!/usr/bin/env python3
"""
Real-World Document Pipeline Test

Tests the complete AI-powered documentation generation pipeline
using real DOCX and PDF files provided by the user.
"""

import json
import asyncio
from pathlib import Path
from ai_doc_gen.input_processing import validate_document, parse_document, extract_structured_content
from ai_doc_gen.agents.managing_agent import ManagingAgent
from ai_doc_gen.agents.review_agent import ReviewAgent
from ai_doc_gen.core.pipeline_orchestrator import PipelineOrchestrator
from ai_doc_gen.core.gap_analyzer import GapAnalyzer
from ai_doc_gen.core.provenance_tracker import ProvenanceTracker
from ai_doc_gen.core.confidence_scoring import ConfidenceScorer

def load_extracted_content(json_file):
    """Load extracted content from JSON file."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Convert back to ExtractedContent objects
    from ai_doc_gen.input_processing.structured_extractor import ExtractedContent, ContentType
    content_items = []
    for item in data:
        content_type = ContentType(item['content_type'])
        content_items.append(ExtractedContent(
            content_type=content_type,
            title=item['title'],
            content=item['content'],
            confidence=item['confidence'],
            source_section=item['source_section'],
            tags=item.get('tags', [])
        ))
    return content_items

async def test_document_pipeline(doc_name, doc_path, extracted_json):
    """Test the complete pipeline for a single document."""
    print(f"\n{'='*80}")
    print(f"TESTING PIPELINE: {doc_name}")
    print(f"{'='*80}")
    
    # Step 1: Load extracted content
    print(f"\nStep 1: Loading extracted content from {extracted_json}")
    extracted_content = load_extracted_content(extracted_json)
    print(f"Loaded {len(extracted_content)} content items")
    
    # Step 2: Managing Agent Analysis
    print(f"\nStep 2: Managing Agent Analysis")
    managing_agent = ManagingAgent()
    managing_results = managing_agent.run(extracted_content)
    
    print(f"  Total content items: {managing_results['total_content_items']}")
    print(f"  Gaps detected: {managing_results['total_gaps']}")
    print(f"  SME questions generated: {managing_results['total_sme_questions']}")
    
    # Show top confidence scores
    confidence_scores = managing_results['confidence_scores']
    top_scores = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"  Top confidence scores:")
    for title, score in top_scores:
        print(f"    {title[:50]}...: {score:.1f}%")
    
    # Step 3: Review Agent Audit
    print(f"\nStep 3: Review Agent Audit")
    review_agent = ReviewAgent()
    
    # Create provenance map
    provenance_map = {
        item.title: f"{doc_name}#{item.source_section}"
        for item in extracted_content
    }
    
    review_results = review_agent.run(extracted_content, provenance_map=provenance_map)
    
    print(f"  Total items audited: {review_results['total_items']}")
    print(f"  Missing provenance: {review_results['total_missing_provenance']}")
    print(f"  Low confidence items: {review_results['total_low_confidence']}")
    
    # Step 4: Pipeline Orchestrator (Full End-to-End)
    print(f"\nStep 4: Full Pipeline Orchestrator")
    
    # Initialize pipeline with configuration
    config = {
        "llm_provider": "openai",
        "confidence_threshold": 85.0,
        "gap_threshold": 70.0
    }
    
    orchestrator = PipelineOrchestrator(config=config)
    
    # Create output directory
    output_dir = f"pipeline_output_{doc_name.lower().replace(' ', '_')}"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Run pipeline
    try:
        pipeline_results = await orchestrator.run_pipeline(
            input_files=[doc_path],
            output_dir=output_dir
        )
        
        print(f"  Pipeline completed successfully!")
        print(f"  Output directory: {output_dir}")
        
        # Show key results
        if 'draft_document' in pipeline_results:
            draft = pipeline_results['draft_document']
            print(f"  Draft sections: {len(draft.get('sections', []))}")
        
        if 'final_metrics' in pipeline_results:
            metrics = pipeline_results['final_metrics']
            print(f"  Processing time: {metrics.get('processing_time', 'N/A')}")
        
    except Exception as e:
        print(f"  Pipeline error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Generate Summary Report
    print(f"\nStep 5: Generating Summary Report")
    
    summary = {
        "document_info": {
            "name": doc_name,
            "path": doc_path,
            "extracted_items": len(extracted_content)
        },
        "managing_agent": {
            "gaps_detected": managing_results['total_gaps'],
            "sme_questions": managing_results['total_sme_questions'],
            "avg_confidence": sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        },
        "review_agent": {
            "items_audited": review_results['total_items'],
            "missing_provenance": review_results['total_missing_provenance'],
            "low_confidence": review_results['total_low_confidence']
        },
        "content_analysis": {
            "content_types": {},
            "high_confidence_items": 0,
            "medium_confidence_items": 0,
            "low_confidence_items": 0
        }
    }
    
    # Analyze content types and confidence levels
    for item in extracted_content:
        content_type = item.content_type.value
        summary["content_analysis"]["content_types"][content_type] = \
            summary["content_analysis"]["content_types"].get(content_type, 0) + 1
        
        if item.confidence >= 0.8:
            summary["content_analysis"]["high_confidence_items"] += 1
        elif item.confidence >= 0.6:
            summary["content_analysis"]["medium_confidence_items"] += 1
        else:
            summary["content_analysis"]["low_confidence_items"] += 1
    
    # Save summary
    summary_file = f"{output_dir}/pipeline_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"  Summary saved to: {summary_file}")
    
    return summary

async def main():
    """Main test function."""
    print("REAL-WORLD DOCUMENT PIPELINE TEST")
    print("="*80)
    
    # Test both documents
    documents = [
        ("Functional Specification", "functional_spec.docx", "functional_spec_extracted.json"),
        ("Installation Guide", "installation_guide.pdf", "installation_guide_extracted.json")
    ]
    
    results = {}
    
    for doc_name, doc_path, extracted_json in documents:
        if Path(extracted_json).exists():
            try:
                summary = await test_document_pipeline(doc_name, doc_path, extracted_json)
                results[doc_name] = summary
            except Exception as e:
                print(f"Error testing {doc_name}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Extracted content file not found: {extracted_json}")
    
    # Generate overall summary
    print(f"\n{'='*80}")
    print("OVERALL TEST SUMMARY")
    print(f"{'='*80}")
    
    total_items = sum(r["document_info"]["extracted_items"] for r in results.values())
    total_gaps = sum(r["managing_agent"]["gaps_detected"] for r in results.values())
    total_questions = sum(r["managing_agent"]["sme_questions"] for r in results.values())
    
    print(f"Total documents processed: {len(results)}")
    print(f"Total content items extracted: {total_items}")
    print(f"Total gaps detected: {total_gaps}")
    print(f"Total SME questions generated: {total_questions}")
    
    # Save overall results
    with open("overall_pipeline_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nOverall results saved to: overall_pipeline_results.json")
    print(f"\nPipeline test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 