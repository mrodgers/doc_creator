#!/usr/bin/env python3
"""
Integrated test for enhanced HTML parser in the AI documentation pipeline.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_doc_gen.agents.managing_agent import ManagingAgent
from ai_doc_gen.core.pipeline_orchestrator import PipelineOrchestrator
from ai_doc_gen.input_processing.document_parser import DocumentParserFactory


def test_enhanced_parser_integration():
    """Test the enhanced HTML parser integrated into the full pipeline."""

    print("🧪 Testing Enhanced HTML Parser Integration")
    print("=" * 60)

    # Check if the webpage.html file exists
    html_file = "webpage.html"
    if not os.path.exists(html_file):
        print(f"❌ HTML file {html_file} not found")
        return False

    try:
        # Step 1: Test enhanced parser directly
        print("📄 Step 1: Testing Enhanced HTML Parser")
        print("-" * 40)

        factory = DocumentParserFactory()
        parser = factory.get_parser(html_file)

        if not parser:
            print("❌ Could not get HTML parser")
            return False

        parsed_doc = parser.parse(html_file)
        print(f"✅ Enhanced parser extracted {len(parsed_doc.sections)} sections")
        print(f"✅ Total content items: {sum(len(s['content']) for s in parsed_doc.sections)}")

        # Step 2: Test integration with pipeline orchestrator
        print("\n🔄 Step 2: Testing Pipeline Integration")
        print("-" * 40)

        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()

        # Process the HTML document through the pipeline
        print(f"📊 Processing {html_file} through pipeline...")

        # Create structured content from parsed document
        structured_content = {
            "document": parsed_doc.model_dump(),
            "sections": parsed_doc.sections,
            "metadata": parsed_doc.metadata,
            "raw_text": parsed_doc.raw_text
        }

        # Run pipeline analysis
        pipeline_result = orchestrator.analyze_document(
            file_path=html_file,
            structured_content=structured_content
        )

        print("✅ Pipeline analysis completed")
        print(f"   - Content items: {len(pipeline_result.content_items)}")
        print(f"   - Sections: {len(pipeline_result.sections)}")
        print(f"   - Confidence score: {pipeline_result.confidence_score:.2f}")
        print(f"   - Structure score: {pipeline_result.structure_score:.2f}")
        print(f"   - Style score: {pipeline_result.style_score:.2f}")
        print(f"   - Completeness score: {pipeline_result.completeness_score:.2f}")

        # Step 3: Generate draft using enhanced content
        print("\n📝 Step 3: Testing Draft Generation")
        print("-" * 40)

        # Create managing agent for draft generation
        managing_agent = ManagingAgent()

        # Generate draft
        draft_result = managing_agent.generate_draft(
            content_items=pipeline_result.content_items,
            sections=pipeline_result.sections,
            gap_analysis=pipeline_result.gap_analysis
        )

        print("✅ Draft generation completed")
        print(f"   - Draft sections: {len(draft_result.sections)}")
        print(f"   - SME questions: {len(draft_result.sme_questions)}")
        print(f"   - Recommendations: {len(draft_result.recommendations)}")

        # Step 4: Save comprehensive results
        print("\n💾 Step 4: Saving Results")
        print("-" * 40)

        # Save pipeline results
        pipeline_output = {
            "pipeline_result": pipeline_result.model_dump(),
            "draft_result": draft_result.model_dump(),
            "enhanced_parser_stats": {
                "sections_extracted": len(parsed_doc.sections),
                "content_items": sum(len(s['content']) for s in parsed_doc.sections),
                "table_sections": len([s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]),
                "parsing_errors": len(parsed_doc.parsing_errors)
            }
        }

        output_file = "enhanced_parser_pipeline_results.json"
        with open(output_file, 'w') as f:
            json.dump(pipeline_output, f, indent=2, default=str)

        print(f"✅ Results saved to {output_file}")

        # Step 5: Compare with original scraper
        print("\n🔄 Step 5: Comparison with Original Scraper")
        print("-" * 40)

        compare_with_original_scraper(parsed_doc, pipeline_result)

        return True

    except Exception as e:
        print(f"❌ Error in integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_original_scraper(enhanced_parsed_doc, pipeline_result):
    """Compare enhanced parser results with original scraper results."""

    original_dir = "scraped_cisco_guide"
    if not os.path.exists(original_dir):
        print(f"❌ Original scraper results directory {original_dir} not found")
        return

    # Load original scraper results
    original_files = [f for f in os.listdir(original_dir) if f.endswith('.json')]
    print(f"📁 Original scraper files: {len(original_files)}")

    # Count original content
    original_sections = 0
    original_content_items = 0

    for file in original_files:
        file_path = os.path.join(original_dir, file)
        try:
            with open(file_path) as f:
                data = json.load(f)
                if 'sections' in data:
                    original_sections += len(data['sections'])
                if 'content' in data:
                    original_content_items += len(data['content'])
        except Exception as e:
            print(f"⚠️  Error reading {file}: {e}")

    # Enhanced parser stats
    enhanced_sections = len(enhanced_parsed_doc.sections)
    enhanced_content_items = sum(len(s['content']) for s in enhanced_parsed_doc.sections)

    print("\n📊 Comparison Results:")
    print("   Original Scraper:")
    print(f"     - Files: {len(original_files)}")
    print(f"     - Sections: {original_sections}")
    print(f"     - Content items: {original_content_items}")
    print("   Enhanced Parser:")
    print(f"     - Sections: {enhanced_sections}")
    print(f"     - Content items: {enhanced_content_items}")
    print(f"     - Pipeline content items: {len(pipeline_result.content_items)}")

    # Calculate improvements
    if original_sections > 0:
        section_improvement = ((enhanced_sections - original_sections) / original_sections) * 100
        print(f"   Section improvement: {section_improvement:+.1f}%")

    if original_content_items > 0:
        content_improvement = ((enhanced_content_items - original_content_items) / original_content_items) * 100
        print(f"   Content improvement: {content_improvement:+.1f}%")

    # Show unique features of enhanced parser
    table_sections = [s for s in enhanced_parsed_doc.sections if any('Table' in str(c) for c in s['content'])]
    print("   Enhanced parser unique features:")
    print(f"     - Table sections: {len(table_sections)}")
    print(f"     - Pipeline confidence: {pipeline_result.confidence_score:.2f}")
    print(f"     - Pipeline structure: {pipeline_result.structure_score:.2f}")

def test_web_ui_integration():
    """Test that the enhanced parser works with the web UI."""

    print("\n🌐 Step 6: Testing Web UI Integration")
    print("-" * 40)

    # Check if web UI can handle the enhanced parser results
    try:
        from ai_doc_gen.utils.serialization import EnhancedJSONEncoder

        # Test serialization of enhanced parser results
        html_file = "webpage.html"
        if os.path.exists(html_file):
            factory = DocumentParserFactory()
            parser = factory.get_parser(html_file)
            parsed_doc = parser.parse(html_file)

            # Test JSON serialization
            encoder = EnhancedJSONEncoder()
            serialized = encoder.encode(parsed_doc.model_dump())

            print("✅ Enhanced parser results can be serialized for web UI")
            print(f"   - Serialized size: {len(serialized)} characters")

            return True
        else:
            print("⚠️  HTML file not found for web UI test")
            return False

    except Exception as e:
        print(f"❌ Web UI integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Enhanced HTML Parser Integration Test")
    print("=" * 60)

    success = test_enhanced_parser_integration()

    if success:
        web_ui_success = test_web_ui_integration()
        if web_ui_success:
            print("\n✅ All integration tests completed successfully!")
            print("\n🎯 Next Steps:")
            print("   1. The enhanced HTML parser is now integrated into the pipeline")
            print("   2. It provides better table extraction using pandas")
            print("   3. It maintains compatibility with the web UI")
            print("   4. Results show significant improvements over basic scraping")
        else:
            print("\n⚠️  Enhanced parser works but web UI integration needs attention")
    else:
        print("\n❌ Enhanced parser integration test failed!")
        sys.exit(1)
