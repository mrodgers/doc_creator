#!/usr/bin/env python3
"""
Comprehensive comparison between PDF and HTML extraction capabilities.
"""

import json
import os
import sys
import time
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_doc_gen.input_processing.document_parser import DocumentParserFactory


class ExtractionComparison:
    """Compare extraction capabilities between PDF and HTML formats."""

    def __init__(self):
        self.factory = DocumentParserFactory()
        self.results = {}

    def extract_from_pdf(self, pdf_file: str) -> Dict[str, Any]:
        """Extract content from PDF file."""
        print(f"📄 Extracting from PDF: {pdf_file}")

        if not os.path.exists(pdf_file):
            print(f"❌ PDF file not found: {pdf_file}")
            return {}

        start_time = time.time()

        try:
            parser = self.factory.get_parser(pdf_file)
            if not parser:
                print(f"❌ No parser available for PDF: {pdf_file}")
                return {}

            parsed_doc = parser.parse(pdf_file)

            extraction_time = time.time() - start_time

            # Analyze content
            sections_with_content = [s for s in parsed_doc.sections if len(s['content']) > 0]
            table_sections = [s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]

            result = {
                "file_type": "pdf",
                "filename": os.path.basename(pdf_file),
                "file_size_bytes": os.path.getsize(pdf_file),
                "extraction_time_seconds": extraction_time,
                "title": parsed_doc.title,
                "total_sections": len(parsed_doc.sections),
                "sections_with_content": len(sections_with_content),
                "total_content_items": sum(len(s['content']) for s in parsed_doc.sections),
                "table_sections": len(table_sections),
                "raw_text_length": len(parsed_doc.raw_text),
                "parsing_errors": len(parsed_doc.parsing_errors),
                "metadata": parsed_doc.metadata,
                "sample_sections": [
                    {
                        "heading": s['heading'],
                        "level": s['level'],
                        "content_count": len(s['content']),
                        "sample_content": s['content'][0][:100] + "..." if s['content'] else ""
                    }
                    for s in sections_with_content[:10]
                ],
                "table_content": [
                    {
                        "heading": s['heading'],
                        "table_count": len([c for c in s['content'] if 'Table' in str(c)]),
                        "sample_table": next((c for c in s['content'] if 'Table' in str(c)), "")[:200] + "..."
                    }
                    for s in table_sections[:5]
                ]
            }

            print(f"✅ PDF extraction completed in {extraction_time:.2f}s")
            print(f"   - Sections: {result['total_sections']}")
            print(f"   - Content items: {result['total_content_items']}")
            print(f"   - Table sections: {result['table_sections']}")

            return result

        except Exception as e:
            print(f"❌ Error extracting from PDF: {e}")
            return {}

    def extract_from_html(self, html_file: str) -> Dict[str, Any]:
        """Extract content from HTML file."""
        print(f"🌐 Extracting from HTML: {html_file}")

        if not os.path.exists(html_file):
            print(f"❌ HTML file not found: {html_file}")
            return {}

        start_time = time.time()

        try:
            parser = self.factory.get_parser(html_file)
            if not parser:
                print(f"❌ No parser available for HTML: {html_file}")
                return {}

            parsed_doc = parser.parse(html_file)

            extraction_time = time.time() - start_time

            # Analyze content
            sections_with_content = [s for s in parsed_doc.sections if len(s['content']) > 0]
            table_sections = [s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]
            enhanced_sections = [s for s in parsed_doc.sections if s.get('source') == 'html_enhanced']

            result = {
                "file_type": "html",
                "filename": os.path.basename(html_file),
                "file_size_bytes": os.path.getsize(html_file),
                "extraction_time_seconds": extraction_time,
                "title": parsed_doc.title,
                "total_sections": len(parsed_doc.sections),
                "sections_with_content": len(sections_with_content),
                "total_content_items": sum(len(s['content']) for s in parsed_doc.sections),
                "table_sections": len(table_sections),
                "enhanced_source_sections": len(enhanced_sections),
                "raw_text_length": len(parsed_doc.raw_text),
                "parsing_errors": len(parsed_doc.parsing_errors),
                "metadata": parsed_doc.metadata,
                "sample_sections": [
                    {
                        "heading": s['heading'],
                        "level": s['level'],
                        "content_count": len(s['content']),
                        "source": s.get('source', 'unknown'),
                        "sample_content": s['content'][0][:100] + "..." if s['content'] else ""
                    }
                    for s in sections_with_content[:10]
                ],
                "table_content": [
                    {
                        "heading": s['heading'],
                        "table_count": len([c for c in s['content'] if 'Table' in str(c)]),
                        "sample_table": next((c for c in s['content'] if 'Table' in str(c)), "")[:200] + "..."
                    }
                    for s in table_sections[:5]
                ]
            }

            print(f"✅ HTML extraction completed in {extraction_time:.2f}s")
            print(f"   - Sections: {result['total_sections']}")
            print(f"   - Content items: {result['total_content_items']}")
            print(f"   - Table sections: {result['table_sections']}")
            print(f"   - Enhanced source: {result['enhanced_source_sections']}")

            return result

        except Exception as e:
            print(f"❌ Error extracting from HTML: {e}")
            return {}

    def compare_extractions(self, pdf_result: Dict[str, Any], html_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare the results of PDF and HTML extractions."""

        print("\n📊 Comparing PDF vs HTML Extraction Results")
        print("=" * 60)

        comparison = {
            "summary": {
                "pdf_file": pdf_result.get("filename", "N/A"),
                "html_file": html_result.get("filename", "N/A"),
                "comparison_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "performance_comparison": {
                "extraction_time": {
                    "pdf_seconds": pdf_result.get("extraction_time_seconds", 0),
                    "html_seconds": html_result.get("extraction_time_seconds", 0),
                    "difference_seconds": (html_result.get("extraction_time_seconds", 0) -
                                         pdf_result.get("extraction_time_seconds", 0)),
                    "faster_format": "PDF" if pdf_result.get("extraction_time_seconds", 0) <
                                    html_result.get("extraction_time_seconds", 0) else "HTML"
                },
                "file_size": {
                    "pdf_bytes": pdf_result.get("file_size_bytes", 0),
                    "html_bytes": html_result.get("file_size_bytes", 0),
                    "size_ratio": html_result.get("file_size_bytes", 1) / max(pdf_result.get("file_size_bytes", 1), 1)
                }
            },
            "content_comparison": {
                "sections": {
                    "pdf_total": pdf_result.get("total_sections", 0),
                    "html_total": html_result.get("total_sections", 0),
                    "difference": html_result.get("total_sections", 0) - pdf_result.get("total_sections", 0),
                    "ratio": html_result.get("total_sections", 1) / max(pdf_result.get("total_sections", 1), 1)
                },
                "content_items": {
                    "pdf_total": pdf_result.get("total_content_items", 0),
                    "html_total": html_result.get("total_content_items", 0),
                    "difference": html_result.get("total_content_items", 0) - pdf_result.get("total_content_items", 0),
                    "ratio": html_result.get("total_content_items", 1) / max(pdf_result.get("total_content_items", 1), 1)
                },
                "table_sections": {
                    "pdf_total": pdf_result.get("table_sections", 0),
                    "html_total": html_result.get("table_sections", 0),
                    "difference": html_result.get("table_sections", 0) - pdf_result.get("table_sections", 0),
                    "ratio": html_result.get("table_sections", 1) / max(pdf_result.get("table_sections", 1), 1)
                },
                "raw_text": {
                    "pdf_length": pdf_result.get("raw_text_length", 0),
                    "html_length": html_result.get("raw_text_length", 0),
                    "difference": html_result.get("raw_text_length", 0) - pdf_result.get("raw_text_length", 0),
                    "ratio": html_result.get("raw_text_length", 1) / max(pdf_result.get("raw_text_length", 1), 1)
                }
            },
            "quality_comparison": {
                "parsing_errors": {
                    "pdf_errors": pdf_result.get("parsing_errors", 0),
                    "html_errors": html_result.get("parsing_errors", 0),
                    "more_reliable": "PDF" if pdf_result.get("parsing_errors", 0) <
                                    html_result.get("parsing_errors", 0) else "HTML"
                },
                "structure_detection": {
                    "pdf_sections_with_content": pdf_result.get("sections_with_content", 0),
                    "html_sections_with_content": html_result.get("sections_with_content", 0),
                    "pdf_content_ratio": pdf_result.get("sections_with_content", 0) / max(pdf_result.get("total_sections", 1), 1),
                    "html_content_ratio": html_result.get("sections_with_content", 0) / max(html_result.get("total_sections", 1), 1)
                }
            },
            "format_specific_features": {
                "pdf_features": {
                    "metadata_available": bool(pdf_result.get("metadata", {})),
                    "page_count": pdf_result.get("metadata", {}).get("pages", "Unknown"),
                    "title_from_metadata": pdf_result.get("metadata", {}).get("title", "Unknown")
                },
                "html_features": {
                    "enhanced_source": html_result.get("enhanced_source_sections", 0),
                    "pandas_integration": True,
                    "beautifulsoup_enhanced": True,
                    "table_extraction": html_result.get("table_sections", 0) > 0
                }
            }
        }

        # Print comparison summary
        print("\n📈 Performance Comparison:")
        print(f"   PDF extraction time: {comparison['performance_comparison']['extraction_time']['pdf_seconds']:.2f}s")
        print(f"   HTML extraction time: {comparison['performance_comparison']['extraction_time']['html_seconds']:.2f}s")
        print(f"   Faster format: {comparison['performance_comparison']['extraction_time']['faster_format']}")

        print("\n📊 Content Comparison:")
        print(f"   PDF sections: {comparison['content_comparison']['sections']['pdf_total']}")
        print(f"   HTML sections: {comparison['content_comparison']['sections']['html_total']}")
        print(f"   PDF content items: {comparison['content_comparison']['content_items']['pdf_total']}")
        print(f"   HTML content items: {comparison['content_comparison']['content_items']['html_total']}")
        print(f"   PDF table sections: {comparison['content_comparison']['table_sections']['pdf_total']}")
        print(f"   HTML table sections: {comparison['content_comparison']['table_sections']['html_total']}")

        print("\n🎯 Quality Comparison:")
        print(f"   PDF parsing errors: {comparison['quality_comparison']['parsing_errors']['pdf_errors']}")
        print(f"   HTML parsing errors: {comparison['quality_comparison']['parsing_errors']['html_errors']}")
        print(f"   More reliable: {comparison['quality_comparison']['parsing_errors']['more_reliable']}")

        return comparison

    def generate_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison results."""

        recommendations = []

        # Performance recommendations
        if comparison['performance_comparison']['extraction_time']['difference_seconds'] > 2:
            faster_format = comparison['performance_comparison']['extraction_time']['faster_format']
            recommendations.append(f"Use {faster_format} format for faster processing")

        # Content recommendations
        if comparison['content_comparison']['sections']['ratio'] > 2:
            recommendations.append("HTML provides significantly more sections - prefer for comprehensive extraction")

        if comparison['content_comparison']['table_sections']['ratio'] > 1.5:
            recommendations.append("HTML provides better table extraction - prefer for technical documentation")

        if comparison['content_comparison']['content_items']['ratio'] > 2:
            recommendations.append("HTML provides significantly more content items - prefer for detailed analysis")

        # Quality recommendations
        if comparison['quality_comparison']['parsing_errors']['pdf_errors'] == 0 and comparison['quality_comparison']['parsing_errors']['html_errors'] > 0:
            recommendations.append("PDF provides more reliable parsing - prefer for critical documents")

        # Feature recommendations
        if comparison['format_specific_features']['html_features']['enhanced_source'] > 0:
            recommendations.append("HTML enhanced parser provides advanced features - prefer for complex documents")

        if comparison['format_specific_features']['html_features']['table_extraction']:
            recommendations.append("HTML provides structured table extraction - prefer for technical specifications")

        return recommendations

def main():
    """Main comparison function."""

    print("🔍 PDF vs HTML Extraction Comparison")
    print("=" * 60)

    # Check for available files
    pdf_file = "installation_guide.pdf"
    html_file = "webpage.html"

    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        print("   Please ensure installation_guide.pdf is available")
        return

    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        print("   Please ensure webpage.html is available")
        return

    # Create comparison object
    comparison_tool = ExtractionComparison()

    # Extract from both formats
    print("\n📄 Step 1: PDF Extraction")
    print("-" * 40)
    pdf_result = comparison_tool.extract_from_pdf(pdf_file)

    print("\n🌐 Step 2: HTML Extraction")
    print("-" * 40)
    html_result = comparison_tool.extract_from_html(html_file)

    if not pdf_result or not html_result:
        print("❌ Extraction failed for one or both formats")
        return

    # Compare results
    print("\n📊 Step 3: Comparison Analysis")
    print("-" * 40)
    comparison = comparison_tool.compare_extractions(pdf_result, html_result)

    # Generate recommendations
    print("\n💡 Step 4: Recommendations")
    print("-" * 40)
    recommendations = comparison_tool.generate_recommendations(comparison)

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   Both formats perform similarly - choose based on source availability")

    # Save detailed results
    print("\n💾 Step 5: Saving Results")
    print("-" * 40)

    detailed_results = {
        "comparison": comparison,
        "pdf_result": pdf_result,
        "html_result": html_result,
        "recommendations": recommendations
    }

    output_file = "pdf_vs_html_comparison_results.json"
    with open(output_file, 'w') as f:
        json.dump(detailed_results, f, indent=2, default=str)

    print(f"✅ Detailed comparison saved to: {output_file}")

    # Print final summary
    print("\n🎯 Final Summary")
    print("=" * 60)
    print(f"📄 PDF Performance: {comparison['performance_comparison']['extraction_time']['pdf_seconds']:.2f}s")
    print(f"🌐 HTML Performance: {comparison['performance_comparison']['extraction_time']['html_seconds']:.2f}s")
    print(f"📊 PDF Content: {comparison['content_comparison']['content_items']['pdf_total']} items")
    print(f"📊 HTML Content: {comparison['content_comparison']['content_items']['html_total']} items")
    print(f"📋 PDF Tables: {comparison['content_comparison']['table_sections']['pdf_total']} sections")
    print(f"📋 HTML Tables: {comparison['content_comparison']['table_sections']['html_total']} sections")

    winner = "HTML" if comparison['content_comparison']['content_items']['html_total'] > comparison['content_comparison']['content_items']['pdf_total'] else "PDF"
    print(f"\n🏆 Overall Winner: {winner} (based on content extraction)")

    print("\n✅ Comparison completed successfully!")

if __name__ == "__main__":
    main()
