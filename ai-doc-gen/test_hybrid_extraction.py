#!/usr/bin/env python3
"""
Hybrid extraction test - combining PDF and HTML for optimal results.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_doc_gen.input_processing.document_parser import DocumentParserFactory

class HybridExtractor:
    """Combine PDF and HTML extraction for optimal results."""
    
    def __init__(self):
        self.factory = DocumentParserFactory()
    
    def extract_hybrid(self, pdf_file: str, html_file: str) -> Dict[str, Any]:
        """Extract content using both PDF and HTML, then combine for optimal results."""
        
        print("🔄 Hybrid Extraction: PDF + HTML")
        print("=" * 60)
        
        # Step 1: Extract from both formats
        print("📄 Step 1: Extracting from both formats")
        print("-" * 40)
        
        pdf_result = self._extract_pdf(pdf_file)
        html_result = self._extract_html(html_file)
        
        if not pdf_result or not html_result:
            print("❌ Extraction failed for one or both formats")
            return {}
        
        # Step 2: Analyze strengths of each format
        print("\n📊 Step 2: Analyzing format strengths")
        print("-" * 40)
        
        pdf_strengths = self._analyze_pdf_strengths(pdf_result)
        html_strengths = self._analyze_html_strengths(html_result)
        
        # Step 3: Combine results intelligently
        print("\n🔗 Step 3: Combining results intelligently")
        print("-" * 40)
        
        combined_result = self._combine_results(pdf_result, html_result, pdf_strengths, html_strengths)
        
        # Step 4: Generate recommendations
        print("\n💡 Step 4: Generating usage recommendations")
        print("-" * 40)
        
        recommendations = self._generate_hybrid_recommendations(combined_result)
        
        return {
            "pdf_result": pdf_result,
            "html_result": html_result,
            "combined_result": combined_result,
            "pdf_strengths": pdf_strengths,
            "html_strengths": html_strengths,
            "recommendations": recommendations
        }
    
    def _extract_pdf(self, pdf_file: str) -> Dict[str, Any]:
        """Extract content from PDF."""
        if not os.path.exists(pdf_file):
            return {}
        
        start_time = time.time()
        parser = self.factory.get_parser(pdf_file)
        parsed_doc = parser.parse(pdf_file)
        extraction_time = time.time() - start_time
        
        sections_with_content = [s for s in parsed_doc.sections if len(s['content']) > 0]
        table_sections = [s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]
        
        return {
            "file_type": "pdf",
            "filename": os.path.basename(pdf_file),
            "extraction_time": extraction_time,
            "total_sections": len(parsed_doc.sections),
            "sections_with_content": len(sections_with_content),
            "total_content_items": sum(len(s['content']) for s in parsed_doc.sections),
            "table_sections": len(table_sections),
            "raw_text_length": len(parsed_doc.raw_text),
            "metadata": parsed_doc.metadata,
            "sections": parsed_doc.sections
        }
    
    def _extract_html(self, html_file: str) -> Dict[str, Any]:
        """Extract content from HTML."""
        if not os.path.exists(html_file):
            return {}
        
        start_time = time.time()
        parser = self.factory.get_parser(html_file)
        parsed_doc = parser.parse(html_file)
        extraction_time = time.time() - start_time
        
        sections_with_content = [s for s in parsed_doc.sections if len(s['content']) > 0]
        table_sections = [s for s in parsed_doc.sections if any('Table' in str(c) for c in s['content'])]
        enhanced_sections = [s for s in parsed_doc.sections if s.get('source') == 'html_enhanced']
        
        return {
            "file_type": "html",
            "filename": os.path.basename(html_file),
            "extraction_time": extraction_time,
            "total_sections": len(parsed_doc.sections),
            "sections_with_content": len(sections_with_content),
            "total_content_items": sum(len(s['content']) for s in parsed_doc.sections),
            "table_sections": len(table_sections),
            "enhanced_source_sections": len(enhanced_sections),
            "raw_text_length": len(parsed_doc.raw_text),
            "metadata": parsed_doc.metadata,
            "sections": parsed_doc.sections
        }
    
    def _analyze_pdf_strengths(self, pdf_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze strengths of PDF extraction."""
        strengths = {
            "content_density": {
                "content_items_per_section": pdf_result['total_content_items'] / max(pdf_result['total_sections'], 1),
                "text_density": pdf_result['raw_text_length'] / max(pdf_result['total_sections'], 1),
                "content_coverage": pdf_result['sections_with_content'] / max(pdf_result['total_sections'], 1)
            },
            "metadata_richness": {
                "has_metadata": bool(pdf_result.get('metadata', {})),
                "page_count": pdf_result.get('metadata', {}).get('pages', 0),
                "title_available": bool(pdf_result.get('metadata', {}).get('title'))
            },
            "content_quality": {
                "total_content_items": pdf_result['total_content_items'],
                "raw_text_length": pdf_result['raw_text_length'],
                "sections_with_content": pdf_result['sections_with_content']
            }
        }
        
        print(f"📄 PDF Strengths:")
        print(f"   - Content density: {strengths['content_density']['content_items_per_section']:.1f} items/section")
        print(f"   - Text density: {strengths['content_density']['text_density']:.0f} chars/section")
        print(f"   - Content coverage: {strengths['content_density']['content_coverage']*100:.1f}%")
        print(f"   - Total content items: {strengths['content_quality']['total_content_items']}")
        
        return strengths
    
    def _analyze_html_strengths(self, html_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze strengths of HTML extraction."""
        strengths = {
            "structure_detection": {
                "total_sections": html_result['total_sections'],
                "enhanced_source_ratio": html_result['enhanced_source_sections'] / max(html_result['total_sections'], 1),
                "table_extraction_ratio": html_result['table_sections'] / max(html_result['total_sections'], 1)
            },
            "processing_efficiency": {
                "extraction_time": html_result['extraction_time'],
                "sections_per_second": html_result['total_sections'] / max(html_result['extraction_time'], 0.001)
            },
            "technical_features": {
                "enhanced_source_sections": html_result['enhanced_source_sections'],
                "table_sections": html_result['table_sections'],
                "pandas_integration": True,
                "beautifulsoup_enhanced": True
            }
        }
        
        print(f"🌐 HTML Strengths:")
        print(f"   - Structure detection: {strengths['structure_detection']['total_sections']} sections")
        print(f"   - Enhanced source: {strengths['structure_detection']['enhanced_source_ratio']*100:.1f}%")
        print(f"   - Table extraction: {strengths['structure_detection']['table_extraction_ratio']*100:.1f}%")
        print(f"   - Processing speed: {strengths['processing_efficiency']['sections_per_second']:.0f} sections/sec")
        
        return strengths
    
    def _combine_results(self, pdf_result: Dict[str, Any], html_result: Dict[str, Any], 
                        pdf_strengths: Dict[str, Any], html_strengths: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently combine PDF and HTML results."""
        
        print(f"🔗 Combining results...")
        
        # Use HTML for structure, PDF for content
        combined_sections = []
        
        # Add HTML sections for structure
        for section in html_result['sections']:
            combined_sections.append({
                "heading": section['heading'],
                "level": section['level'],
                "source": "html_structure",
                "content": section['content'],
                "html_enhanced": section.get('source') == 'html_enhanced'
            })
        
        # Add PDF content where available
        pdf_content_by_heading = {}
        for section in pdf_result['sections']:
            if section['content']:
                pdf_content_by_heading[section['heading'].lower()] = section['content']
        
        # Merge content where headings match
        merged_count = 0
        for section in combined_sections:
            heading_lower = section['heading'].lower()
            if heading_lower in pdf_content_by_heading:
                # Combine HTML structure with PDF content
                section['content'].extend(pdf_content_by_heading[heading_lower])
                section['source'] = "hybrid_merged"
                merged_count += 1
        
        # Calculate combined metrics
        total_content_items = sum(len(s['content']) for s in combined_sections)
        table_sections = len([s for s in combined_sections if any('Table' in str(c) for c in s['content'])])
        enhanced_sections = len([s for s in combined_sections if s.get('html_enhanced', False)])
        
        combined_result = {
            "total_sections": len(combined_sections),
            "total_content_items": total_content_items,
            "table_sections": table_sections,
            "enhanced_sections": enhanced_sections,
            "merged_sections": merged_count,
            "sections": combined_sections,
            "combined_metadata": {
                "pdf_metadata": pdf_result.get('metadata', {}),
                "html_metadata": html_result.get('metadata', {}),
                "extraction_times": {
                    "pdf": pdf_result['extraction_time'],
                    "html": html_result['extraction_time'],
                    "total": pdf_result['extraction_time'] + html_result['extraction_time']
                }
            }
        }
        
        print(f"✅ Combined results:")
        print(f"   - Total sections: {combined_result['total_sections']}")
        print(f"   - Total content items: {combined_result['total_content_items']}")
        print(f"   - Table sections: {combined_result['table_sections']}")
        print(f"   - Merged sections: {combined_result['merged_sections']}")
        
        return combined_result
    
    def _generate_hybrid_recommendations(self, combined_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for hybrid usage."""
        
        recommendations = []
        
        # Performance recommendations
        total_time = combined_result['combined_metadata']['extraction_times']['total']
        if total_time < 3:
            recommendations.append("Hybrid extraction is fast enough for real-time processing")
        else:
            recommendations.append("Consider caching hybrid results for repeated access")
        
        # Content recommendations
        if combined_result['merged_sections'] > 0:
            recommendations.append(f"Successfully merged {combined_result['merged_sections']} sections from both formats")
        
        if combined_result['table_sections'] > 10:
            recommendations.append("Excellent table extraction - suitable for technical documentation")
        
        if combined_result['enhanced_sections'] > 100:
            recommendations.append("Strong structure detection - good for complex documents")
        
        # Quality recommendations
        content_per_section = combined_result['total_content_items'] / max(combined_result['total_sections'], 1)
        if content_per_section > 5:
            recommendations.append("High content density - comprehensive extraction achieved")
        
        return recommendations

def main():
    """Main hybrid extraction test."""
    
    print("🚀 Hybrid PDF + HTML Extraction Test")
    print("=" * 60)
    
    # Check for available files
    pdf_file = "installation_guide.pdf"
    html_file = "webpage.html"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        return
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return
    
    # Create hybrid extractor
    hybrid_extractor = HybridExtractor()
    
    # Run hybrid extraction
    results = hybrid_extractor.extract_hybrid(pdf_file, html_file)
    
    if not results:
        print("❌ Hybrid extraction failed")
        return
    
    # Save results
    print("\n💾 Saving hybrid results")
    print("-" * 40)
    
    output_file = "hybrid_extraction_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✅ Hybrid results saved to: {output_file}")
    
    # Print final summary
    print("\n🎯 Hybrid Extraction Summary")
    print("=" * 60)
    
    combined = results['combined_result']
    pdf = results['pdf_result']
    html = results['html_result']
    
    print(f"📄 PDF Contribution:")
    print(f"   - Sections: {pdf['total_sections']}")
    print(f"   - Content items: {pdf['total_content_items']}")
    print(f"   - Extraction time: {pdf['extraction_time']:.2f}s")
    
    print(f"\n🌐 HTML Contribution:")
    print(f"   - Sections: {html['total_sections']}")
    print(f"   - Content items: {html['total_content_items']}")
    print(f"   - Extraction time: {html['extraction_time']:.2f}s")
    
    print(f"\n🔗 Combined Results:")
    print(f"   - Total sections: {combined['total_sections']}")
    print(f"   - Total content items: {combined['total_content_items']}")
    print(f"   - Table sections: {combined['table_sections']}")
    print(f"   - Merged sections: {combined['merged_sections']}")
    print(f"   - Total time: {combined['combined_metadata']['extraction_times']['total']:.2f}s")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Calculate improvement
    pdf_content = pdf['total_content_items']
    html_content = html['total_content_items']
    combined_content = combined['total_content_items']
    
    improvement_over_pdf = ((combined_content - pdf_content) / pdf_content) * 100 if pdf_content > 0 else 0
    improvement_over_html = ((combined_content - html_content) / html_content) * 100 if html_content > 0 else 0
    
    print(f"\n📈 Improvement Analysis:")
    print(f"   - Combined vs PDF: {improvement_over_pdf:+.1f}%")
    print(f"   - Combined vs HTML: {improvement_over_html:+.1f}%")
    
    print(f"\n✅ Hybrid extraction completed successfully!")

if __name__ == "__main__":
    main() 