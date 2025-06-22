#!/usr/bin/env python3
"""
1:1 Model Comparison Script
Compares extraction results from the same document in PDF vs HTML formats.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.ai_doc_gen.input_processing.document_parser import (
    HTMLParser,
    ParsedDocument,
    PDFParser,
)
from src.ai_doc_gen.utils.serialization import EnhancedJSONEncoder


class ModelComparison1to1:
    """Performs 1:1 comparison between PDF and HTML extraction models."""

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.html_parser = HTMLParser()
        self.results = {}

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract content from PDF document."""
        print(f"📄 Extracting from PDF: {pdf_path}")
        start_time = time.time()

        try:
            document = self.pdf_parser.parse(pdf_path)
            extraction_time = time.time() - start_time

            return {
                'success': True,
                'document': document,
                'extraction_time': extraction_time,
                'format': 'PDF'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'extraction_time': time.time() - start_time,
                'format': 'PDF'
            }

    def extract_from_html(self, html_path: str) -> Dict[str, Any]:
        """Extract content from HTML document."""
        print(f"🌐 Extracting from HTML: {html_path}")
        start_time = time.time()

        try:
            document = self.html_parser.parse(html_path)
            extraction_time = time.time() - start_time

            return {
                'success': True,
                'document': document,
                'extraction_time': extraction_time,
                'format': 'HTML'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'extraction_time': time.time() - start_time,
                'format': 'HTML'
            }

    def analyze_document_structure(self, document: ParsedDocument) -> Dict[str, Any]:
        """Analyze document structure and content metrics."""
        if not document or not document.sections:
            return {
                'section_count': 0,
                'content_item_count': 0,
                'total_text_length': 0,
                'table_count': 0,
                'image_count': 0,
                'list_count': 0,
                'code_block_count': 0
            }

        total_text_length = len(document.raw_text) if document.raw_text else 0
        table_count = 0
        image_count = 0
        list_count = 0
        code_block_count = 0
        content_item_count = 0

        for section in document.sections:
            if section.get('content'):
                content_item_count += len(section['content'])

                # Count different content types (basic analysis)
                for content in section['content']:
                    if isinstance(content, str):
                        if 'table' in content.lower():
                            table_count += 1
                        elif 'list' in content.lower():
                            list_count += 1
                        elif 'code' in content.lower():
                            code_block_count += 1

        return {
            'section_count': len(document.sections),
            'content_item_count': content_item_count,
            'total_text_length': total_text_length,
            'table_count': table_count,
            'image_count': image_count,
            'list_count': list_count,
            'code_block_count': code_block_count
        }

    def compare_section_content(self, pdf_sections: List[Dict], html_sections: List[Dict]) -> Dict[str, Any]:
        """Compare section content between PDF and HTML."""
        pdf_section_titles = [s.get('heading', '') for s in pdf_sections] if pdf_sections else []
        html_section_titles = [s.get('heading', '') for s in html_sections] if html_sections else []

        # Find common sections
        common_sections = set(pdf_section_titles) & set(html_section_titles)
        pdf_only = set(pdf_section_titles) - set(html_section_titles)
        html_only = set(html_section_titles) - set(pdf_section_titles)

        # Compare content in common sections
        common_section_analysis = {}
        for title in common_sections:
            pdf_section = next((s for s in pdf_sections if s.get('heading') == title), None)
            html_section = next((s for s in html_sections if s.get('heading') == title), None)

            if pdf_section and html_section:
                pdf_items = len(pdf_section.get('content', []))
                html_items = len(html_section.get('content', []))

                common_section_analysis[title] = {
                    'pdf_content_items': pdf_items,
                    'html_content_items': html_items,
                    'difference': abs(pdf_items - html_items),
                    'pdf_has_more': pdf_items > html_items
                }

        return {
            'common_sections': list(common_sections),
            'pdf_only_sections': list(pdf_only),
            'html_only_sections': list(html_only),
            'common_section_analysis': common_section_analysis,
            'total_common_sections': len(common_sections),
            'total_pdf_only': len(pdf_only),
            'total_html_only': len(html_only)
        }

    def run_comparison(self, pdf_path: str, html_path: str) -> Dict[str, Any]:
        """Run the complete 1:1 comparison."""
        print("🔍 Starting 1:1 Model Comparison")
        print("=" * 50)

        # Extract from both formats
        pdf_result = self.extract_from_pdf(pdf_path)
        html_result = self.extract_from_html(html_path)

        # Analyze results
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'pdf_result': pdf_result,
            'html_result': html_result,
            'performance_comparison': {},
            'content_comparison': {},
            'structure_comparison': {},
            'recommendations': []
        }

        # Performance comparison
        if pdf_result['success'] and html_result['success']:
            comparison['performance_comparison'] = {
                'pdf_extraction_time': pdf_result['extraction_time'],
                'html_extraction_time': html_result['extraction_time'],
                'speed_difference': abs(pdf_result['extraction_time'] - html_result['extraction_time']),
                'faster_format': 'PDF' if pdf_result['extraction_time'] < html_result['extraction_time'] else 'HTML'
            }

        # Content analysis
        if pdf_result['success'] and pdf_result['document']:
            comparison['structure_comparison']['pdf_analysis'] = self.analyze_document_structure(pdf_result['document'])

        if html_result['success'] and html_result['document']:
            comparison['structure_comparison']['html_analysis'] = self.analyze_document_structure(html_result['document'])

        # Section comparison
        if (pdf_result['success'] and html_result['success'] and
            pdf_result['document'] and html_result['document']):
            comparison['content_comparison'] = self.compare_section_content(
                pdf_result['document'].sections,
                html_result['document'].sections
            )

        # Generate recommendations
        comparison['recommendations'] = self.generate_recommendations(comparison)

        self.results = comparison
        return comparison

    def generate_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []

        # Check if both extractions succeeded
        if not comparison['pdf_result']['success'] or not comparison['html_result']['success']:
            if not comparison['pdf_result']['success']:
                recommendations.append("PDF extraction failed - check PDF format and content")
            if not comparison['html_result']['success']:
                recommendations.append("HTML extraction failed - check HTML structure and accessibility")
            return recommendations

        # Performance recommendations
        perf = comparison['performance_comparison']
        if 'speed_difference' in perf and perf['speed_difference'] > 2.0:
            recommendations.append(f"Significant performance difference: {perf['faster_format']} is {perf['speed_difference']:.2f}s faster")

        # Content recommendations
        if 'structure_comparison' in comparison:
            pdf_analysis = comparison['structure_comparison'].get('pdf_analysis', {})
            html_analysis = comparison['structure_comparison'].get('html_analysis', {})

            if pdf_analysis and html_analysis:
                # Compare content richness
                pdf_items = pdf_analysis.get('content_item_count', 0)
                html_items = html_analysis.get('content_item_count', 0)

                if abs(pdf_items - html_items) > 10:
                    recommendations.append(f"Content difference: PDF has {pdf_items} items, HTML has {html_items} items")

                # Compare table extraction
                pdf_tables = pdf_analysis.get('table_count', 0)
                html_tables = html_analysis.get('table_count', 0)

                if abs(pdf_tables - html_tables) > 0:
                    recommendations.append(f"Table extraction difference: PDF found {pdf_tables} tables, HTML found {html_tables} tables")

        # Section coverage recommendations
        if 'content_comparison' in comparison:
            content_comp = comparison['content_comparison']
            if content_comp.get('total_pdf_only', 0) > 0:
                recommendations.append(f"PDF has {content_comp['total_pdf_only']} unique sections not found in HTML")
            if content_comp.get('total_html_only', 0) > 0:
                recommendations.append(f"HTML has {content_comp['total_html_only']} unique sections not found in PDF")

        if not recommendations:
            recommendations.append("Both formats performed similarly - consider using the faster format")

        return recommendations

    def print_summary(self):
        """Print a human-readable summary of the comparison."""
        if not self.results:
            print("No comparison results available")
            return

        print("\n" + "="*60)
        print("📊 1:1 MODEL COMPARISON SUMMARY")
        print("="*60)

        # Performance
        if 'performance_comparison' in self.results:
            perf = self.results['performance_comparison']
            if perf:
                print("\n⚡ PERFORMANCE:")
                print(f"   PDF extraction: {perf.get('pdf_extraction_time', 'N/A'):.2f}s")
                print(f"   HTML extraction: {perf.get('html_extraction_time', 'N/A'):.2f}s")
                print(f"   Faster format: {perf.get('faster_format', 'N/A')}")

        # Structure comparison
        if 'structure_comparison' in self.results:
            struct = self.results['structure_comparison']
            print("\n📋 CONTENT STRUCTURE:")

            if 'pdf_analysis' in struct:
                pdf = struct['pdf_analysis']
                print(f"   PDF: {pdf.get('section_count', 0)} sections, {pdf.get('content_item_count', 0)} items, {pdf.get('table_count', 0)} tables")

            if 'html_analysis' in struct:
                html = struct['html_analysis']
                print(f"   HTML: {html.get('section_count', 0)} sections, {html.get('content_item_count', 0)} items, {html.get('table_count', 0)} tables")

        # Content comparison
        if 'content_comparison' in self.results:
            content = self.results['content_comparison']
            print("\n🔄 CONTENT OVERLAP:")
            print(f"   Common sections: {content.get('total_common_sections', 0)}")
            print(f"   PDF-only sections: {content.get('total_pdf_only', 0)}")
            print(f"   HTML-only sections: {content.get('total_html_only', 0)}")

        # Recommendations
        if 'recommendations' in self.results:
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")

        print("\n" + "="*60)

    def save_results(self, output_path: str):
        """Save comparison results to JSON file."""
        if not self.results:
            print("No results to save")
            return

        try:
            with open(output_path, 'w') as f:
                json.dump(self.results, f, cls=EnhancedJSONEncoder, indent=2)
            print(f"✅ Results saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


def main():
    """Main function to run the 1:1 comparison."""
    # File paths
    pdf_path = "installation_guide.pdf"
    html_path = "webpage.html"
    output_path = "model_comparison_1to1_results.json"

    # Check if files exist
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return

    if not Path(html_path).exists():
        print(f"❌ HTML file not found: {html_path}")
        return

    # Run comparison
    comparator = ModelComparison1to1()
    results = comparator.run_comparison(pdf_path, html_path)

    # Print summary
    comparator.print_summary()

    # Save results
    comparator.save_results(output_path)

    print(f"\n🎯 Comparison complete! Check {output_path} for detailed results.")


if __name__ == "__main__":
    main()
