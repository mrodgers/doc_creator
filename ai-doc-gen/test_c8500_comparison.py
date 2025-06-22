#!/usr/bin/env python3
"""
Test C8500 PDF vs HTML Comparison
Downloads the HTML page and compares extraction efficacy with the PDF.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests

from src.ai_doc_gen.input_processing.document_parser import (
    HTMLParser,
    PDFParser,
)
from src.ai_doc_gen.utils.serialization import EnhancedJSONEncoder


def download_c8500_html():
    """Download the C8500 HTML page for comparison."""
    url = "https://www.cisco.com/c/en/us/td/docs/routers/cloud_edge/c8500/hardware-installation-guide/b_C8500_HIG/m_Installation.html"

    print(f"🌐 Downloading C8500 HTML from: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        output_file = "b_C8500.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print(f"✅ Downloaded {len(response.text)} characters to {output_file}")
        print(f"📄 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")

        return output_file

    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading document: {e}")
        return None


def extract_and_analyze(pdf_path: str, html_path: str) -> Dict[str, Any]:
    """Extract content from both formats and analyze efficacy."""

    pdf_parser = PDFParser()
    html_parser = HTMLParser()

    results = {
        'timestamp': datetime.now().isoformat(),
        'pdf_analysis': {},
        'html_analysis': {},
        'efficacy_comparison': {},
        'recommendations': []
    }

    # Extract from PDF
    print(f"📄 Extracting from PDF: {pdf_path}")
    pdf_start = time.time()
    try:
        pdf_doc = pdf_parser.parse(pdf_path)
        pdf_time = time.time() - pdf_start
        results['pdf_analysis'] = {
            'success': True,
            'extraction_time': pdf_time,
            'sections': len(pdf_doc.sections),
            'raw_text_length': len(pdf_doc.raw_text),
            'metadata': pdf_doc.metadata,
            'parsing_errors': pdf_doc.parsing_errors
        }
        print(f"   ✅ PDF: {len(pdf_doc.sections)} sections, {len(pdf_doc.raw_text)} chars")
    except Exception as e:
        results['pdf_analysis'] = {
            'success': False,
            'error': str(e),
            'extraction_time': time.time() - pdf_start
        }
        print(f"   ❌ PDF extraction failed: {e}")

    # Extract from HTML
    print(f"🌐 Extracting from HTML: {html_path}")
    html_start = time.time()
    try:
        html_doc = html_parser.parse(html_path)
        html_time = time.time() - html_start
        results['html_analysis'] = {
            'success': True,
            'extraction_time': html_time,
            'sections': len(html_doc.sections),
            'raw_text_length': len(html_doc.raw_text),
            'metadata': html_doc.metadata,
            'parsing_errors': html_doc.parsing_errors
        }
        print(f"   ✅ HTML: {len(html_doc.sections)} sections, {len(html_doc.raw_text)} chars")
    except Exception as e:
        results['html_analysis'] = {
            'success': False,
            'error': str(e),
            'extraction_time': time.time() - html_start
        }
        print(f"   ❌ HTML extraction failed: {e}")

    # Compare efficacy
    if results['pdf_analysis'].get('success') and results['html_analysis'].get('success'):
        pdf_analysis = results['pdf_analysis']
        html_analysis = results['html_analysis']

        results['efficacy_comparison'] = {
            'speed': {
                'pdf_time': pdf_analysis['extraction_time'],
                'html_time': html_analysis['extraction_time'],
                'faster_format': 'PDF' if pdf_analysis['extraction_time'] < html_analysis['extraction_time'] else 'HTML',
                'speed_difference': abs(pdf_analysis['extraction_time'] - html_analysis['extraction_time'])
            },
            'content_richness': {
                'pdf_sections': pdf_analysis['sections'],
                'html_sections': html_analysis['sections'],
                'pdf_text_length': pdf_analysis['raw_text_length'],
                'html_text_length': html_analysis['raw_text_length'],
                'section_ratio': html_analysis['sections'] / pdf_analysis['sections'] if pdf_analysis['sections'] > 0 else 0,
                'text_ratio': html_analysis['raw_text_length'] / pdf_analysis['raw_text_length'] if pdf_analysis['raw_text_length'] > 0 else 0
            },
            'quality': {
                'pdf_errors': len(pdf_analysis.get('parsing_errors', [])),
                'html_errors': len(html_analysis.get('parsing_errors', [])),
                'pdf_has_errors': len(pdf_analysis.get('parsing_errors', [])) > 0,
                'html_has_errors': len(html_analysis.get('parsing_errors', [])) > 0
            }
        }

        # Generate recommendations
        recommendations = []

        # Speed recommendations
        speed_diff = results['efficacy_comparison']['speed']['speed_difference']
        if speed_diff > 1.0:
            faster = results['efficacy_comparison']['speed']['faster_format']
            recommendations.append(f"Performance: {faster} is {speed_diff:.2f}s faster")

        # Content recommendations
        section_ratio = results['efficacy_comparison']['content_richness']['section_ratio']
        text_ratio = results['efficacy_comparison']['content_richness']['text_ratio']

        if section_ratio > 1.5:
            recommendations.append(f"HTML extracts {section_ratio:.1f}x more sections than PDF")
        elif section_ratio < 0.7:
            recommendations.append(f"PDF extracts {1/section_ratio:.1f}x more sections than HTML")

        if text_ratio > 1.3:
            recommendations.append(f"HTML extracts {text_ratio:.1f}x more text than PDF")
        elif text_ratio < 0.8:
            recommendations.append(f"PDF extracts {1/text_ratio:.1f}x more text than HTML")

        # Quality recommendations
        if results['efficacy_comparison']['quality']['pdf_has_errors']:
            recommendations.append(f"PDF has {results['efficacy_comparison']['quality']['pdf_errors']} parsing errors")
        if results['efficacy_comparison']['quality']['html_has_errors']:
            recommendations.append(f"HTML has {results['efficacy_comparison']['quality']['html_errors']} parsing errors")

        if not recommendations:
            recommendations.append("Both formats performed similarly - consider using the faster format")

        results['recommendations'] = recommendations

    return results


def print_efficacy_summary(results: Dict[str, Any]):
    """Print a focused efficacy summary."""
    print("\n" + "="*60)
    print("📊 C8500 PDF vs HTML EFFICACY COMPARISON")
    print("="*60)

    # Basic results
    pdf_success = results['pdf_analysis'].get('success', False)
    html_success = results['html_analysis'].get('success', False)

    print("\n✅ EXTRACTION STATUS:")
    print(f"   PDF: {'SUCCESS' if pdf_success else 'FAILED'}")
    print(f"   HTML: {'SUCCESS' if html_success else 'FAILED'}")

    if not (pdf_success and html_success):
        if not pdf_success:
            print(f"   PDF Error: {results['pdf_analysis'].get('error', 'Unknown')}")
        if not html_success:
            print(f"   HTML Error: {results['html_analysis'].get('error', 'Unknown')}")
        return

    # Efficacy metrics
    if 'efficacy_comparison' in results:
        eff = results['efficacy_comparison']

        print("\n⚡ PERFORMANCE:")
        print(f"   PDF: {eff['speed']['pdf_time']:.2f}s")
        print(f"   HTML: {eff['speed']['html_time']:.2f}s")
        print(f"   Winner: {eff['speed']['faster_format']} ({eff['speed']['speed_difference']:.2f}s faster)")

        print("\n📋 CONTENT RICHNESS:")
        print(f"   PDF: {eff['content_richness']['pdf_sections']} sections, {eff['content_richness']['pdf_text_length']:,} chars")
        print(f"   HTML: {eff['content_richness']['html_sections']} sections, {eff['content_richness']['html_text_length']:,} chars")
        print(f"   Section ratio: {eff['content_richness']['section_ratio']:.2f}x")
        print(f"   Text ratio: {eff['content_richness']['text_ratio']:.2f}x")

        print("\n🔍 QUALITY:")
        print(f"   PDF errors: {eff['quality']['pdf_errors']}")
        print(f"   HTML errors: {eff['quality']['html_errors']}")

    # Recommendations
    if results.get('recommendations'):
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")

    print("\n" + "="*60)


def save_test_results(results: Dict[str, Any], output_path: str):
    """Save test results to JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, cls=EnhancedJSONEncoder, indent=2)
        print(f"✅ Test results saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Main test function."""
    print("🧪 C8500 PDF vs HTML Efficacy Test")
    print("=" * 50)

    # Download HTML
    html_file = download_c8500_html()
    if not html_file:
        print("❌ Failed to download HTML - cannot proceed with comparison")
        return

    # Check if PDF exists
    pdf_file = "b_C8500_HIG.pdf"
    if not Path(pdf_file).exists():
        print(f"❌ PDF file not found: {pdf_file}")
        print("   Please place b_C8500_HIG.pdf in the current directory")
        return

    # Run efficacy test
    print("\n🔍 Running efficacy comparison...")
    results = extract_and_analyze(pdf_file, html_file)

    # Print summary
    print_efficacy_summary(results)

    # Save results
    output_file = "c8500_efficacy_test_results.json"
    save_test_results(results, output_file)

    print(f"\n🎯 Efficacy test complete! Check {output_file} for detailed results.")


if __name__ == "__main__":
    main()
