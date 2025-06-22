#!/usr/bin/env python3
"""
LLM Superset Template Generator
Uses LLM to compare and combine PDF/HTML content into a comprehensive template.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai

from src.ai_doc_gen.input_processing.document_parser import (
    HTMLParser,
    PDFParser,
)
from src.ai_doc_gen.utils.serialization import EnhancedJSONEncoder


@dataclass
class ContentComparison:
    """Structured comparison results."""
    pdf_sections: List[Dict]
    html_sections: List[Dict]
    common_sections: List[str]
    pdf_only_sections: List[str]
    html_only_sections: List[str]
    content_gaps: List[str]
    content_overlaps: List[str]


class LLMSupersetTemplateGenerator:
    """Uses LLM to create comprehensive templates from multiple sources."""

    def __init__(self, api_key: Optional[str] = None):
        self.pdf_parser = PDFParser()
        self.html_parser = HTMLParser()
        self.client = None

        if api_key:
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
        else:
            # Try to get from environment
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
            else:
                print("⚠️  No OpenAI API key found. LLM features will be disabled.")

    def extract_content(self, pdf_path: str, html_path: str) -> Dict[str, Any]:
        """Extract content from both PDF and HTML."""
        print("📄 Extracting content from both formats...")

        results = {
            'pdf_content': None,
            'html_content': None,
            'extraction_errors': []
        }

        # Extract PDF
        try:
            pdf_doc = self.pdf_parser.parse(pdf_path)
            results['pdf_content'] = {
                'sections': pdf_doc.sections,
                'raw_text': pdf_doc.raw_text,
                'metadata': pdf_doc.metadata,
                'title': pdf_doc.title
            }
            print(f"   ✅ PDF: {len(pdf_doc.sections)} sections extracted")
        except Exception as e:
            error_msg = f"PDF extraction failed: {e}"
            results['extraction_errors'].append(error_msg)
            print(f"   ❌ {error_msg}")

        # Extract HTML
        try:
            html_doc = self.html_parser.parse(html_path)
            results['html_content'] = {
                'sections': html_doc.sections,
                'raw_text': html_doc.raw_text,
                'metadata': html_doc.metadata,
                'title': html_doc.title
            }
            print(f"   ✅ HTML: {len(html_doc.sections)} sections extracted")
        except Exception as e:
            error_msg = f"HTML extraction failed: {e}"
            results['extraction_errors'].append(error_msg)
            print(f"   ❌ {error_msg}")

        return results

    def analyze_content_with_llm(self, pdf_content: Dict, html_content: Dict) -> Dict[str, Any]:
        """Use LLM to analyze and compare content from both sources."""
        if not self.client:
            print("❌ LLM client not available - skipping LLM analysis")
            return {}

        print("🤖 Using LLM to analyze content differences...")

        # Prepare content for LLM analysis
        pdf_sections = pdf_content.get('sections', [])
        html_sections = html_content.get('sections', [])

        # Create a summary for LLM
        pdf_summary = self._create_content_summary(pdf_sections, "PDF")
        html_summary = self._create_content_summary(html_sections, "HTML")

        # LLM prompt for content analysis
        prompt = f"""
You are an expert technical documentation analyst. Compare these two content sources for a Cisco hardware installation guide:

PDF CONTENT SUMMARY:
{pdf_summary}

HTML CONTENT SUMMARY:
{html_summary}

Analyze the differences and provide:

1. CONTENT GAPS: What important information is missing from each source?
2. CONTENT OVERLAPS: What information is present in both sources?
3. QUALITY DIFFERENCES: Which source has better quality for specific types of content?
4. TEMPLATE RECOMMENDATIONS: How should future documentation combine the best of both?

Focus on:
- Technical specifications and procedures
- Installation steps and requirements
- Safety information and warnings
- Troubleshooting guidance
- Configuration examples

Provide your analysis in JSON format with these keys:
- content_gaps: list of missing information
- content_overlaps: list of shared information  
- quality_assessment: dict with "pdf_strengths", "html_strengths", "pdf_weaknesses", "html_weaknesses"
- template_recommendations: list of recommendations for future templates
- section_mapping: dict mapping similar sections between formats
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )

            # Parse LLM response
            llm_response = response.choices[0].message.content
            analysis = self._parse_llm_response(llm_response)

            print("   ✅ LLM analysis complete")
            return analysis

        except Exception as e:
            print(f"   ❌ LLM analysis failed: {e}")
            return {}

    def _create_content_summary(self, sections: List[Dict], source_name: str) -> str:
        """Create a summary of content for LLM analysis."""
        if not sections:
            return f"{source_name}: No sections found"

        summary_parts = [f"{source_name} Content Summary:"]

        for i, section in enumerate(sections[:10]):  # Limit to first 10 sections
            heading = section.get('heading', f'Section {i+1}')
            content_count = len(section.get('content', []))
            summary_parts.append(f"- {heading}: {content_count} content items")

        if len(sections) > 10:
            summary_parts.append(f"- ... and {len(sections) - 10} more sections")

        return "\n".join(summary_parts)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback: create structured response from text
                return {
                    'raw_response': response,
                    'content_gaps': [],
                    'content_overlaps': [],
                    'quality_assessment': {},
                    'template_recommendations': []
                }
        except json.JSONDecodeError:
            return {
                'raw_response': response,
                'content_gaps': [],
                'content_overlaps': [],
                'quality_assessment': {},
                'template_recommendations': []
            }

    def generate_superset_template(self, pdf_content: Dict, html_content: Dict, llm_analysis: Dict) -> Dict[str, Any]:
        """Generate a comprehensive superset template."""
        print("🔧 Generating superset template...")

        template = {
            'template_metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_documents': ['PDF', 'HTML'],
                'device_family': 'Cisco Catalyst 8500 Series',
                'template_version': '1.0',
                'description': 'Comprehensive template combining best content from PDF and HTML sources'
            },
            'template_structure': {
                'required_sections': [],
                'optional_sections': [],
                'section_hierarchy': [],
                'content_types': []
            },
            'content_guidelines': {
                'pdf_best_practices': [],
                'html_best_practices': [],
                'combined_approaches': []
            },
            'quality_standards': {
                'minimum_content_requirements': [],
                'validation_criteria': [],
                'completeness_metrics': []
            }
        }

        # Analyze section patterns
        pdf_sections = pdf_content.get('sections', [])
        html_sections = html_content.get('sections', [])

        # Extract section titles and patterns
        pdf_titles = [s.get('heading', '') for s in pdf_sections if s.get('heading')]
        html_titles = [s.get('heading', '') for s in html_sections if s.get('heading')]

        # Identify common patterns
        common_patterns = self._identify_common_patterns(pdf_titles, html_titles)

        # Build template structure
        template['template_structure']['required_sections'] = self._identify_required_sections(pdf_titles, html_titles)
        template['template_structure']['section_hierarchy'] = self._create_section_hierarchy(pdf_sections, html_sections)
        template['content_guidelines'] = self._extract_content_guidelines(llm_analysis)
        template['quality_standards'] = self._define_quality_standards(pdf_content, html_content, llm_analysis)

        print("   ✅ Superset template generated")
        return template

    def _identify_common_patterns(self, pdf_titles: List[str], html_titles: List[str]) -> List[str]:
        """Identify common section patterns between formats."""
        patterns = []

        # Look for common keywords
        common_keywords = ['installation', 'configuration', 'specifications', 'troubleshooting', 'safety', 'requirements']

        for keyword in common_keywords:
            pdf_matches = [title for title in pdf_titles if keyword.lower() in title.lower()]
            html_matches = [title for title in html_titles if keyword.lower() in title.lower()]

            if pdf_matches or html_matches:
                patterns.append({
                    'keyword': keyword,
                    'pdf_sections': pdf_matches,
                    'html_sections': html_matches,
                    'common': list(set(pdf_matches) & set(html_matches))
                })

        return patterns

    def _identify_required_sections(self, pdf_titles: List[str], html_titles: List[str]) -> List[str]:
        """Identify sections that should be required in future templates."""
        required_sections = []

        # Sections that appear in both formats are likely required
        common_sections = list(set(pdf_titles) & set(html_titles))

        # Add critical sections that should always be present
        critical_keywords = ['installation', 'safety', 'requirements', 'specifications']
        for keyword in critical_keywords:
            matching_sections = [s for s in common_sections if keyword.lower() in s.lower()]
            required_sections.extend(matching_sections)

        return list(set(required_sections))  # Remove duplicates

    def _create_section_hierarchy(self, pdf_sections: List[Dict], html_sections: List[Dict]) -> List[Dict]:
        """Create a hierarchical structure for the template."""
        hierarchy = []

        # Combine sections from both sources
        all_sections = []

        for section in pdf_sections:
            all_sections.append({
                'title': section.get('heading', ''),
                'source': 'PDF',
                'level': section.get('level', 1),
                'content_count': len(section.get('content', []))
            })

        for section in html_sections:
            all_sections.append({
                'title': section.get('heading', ''),
                'source': 'HTML',
                'level': section.get('level', 1),
                'content_count': len(section.get('content', []))
            })

        # Group by similar titles
        grouped_sections = {}
        for section in all_sections:
            title = section['title'].lower().strip()
            if title not in grouped_sections:
                grouped_sections[title] = []
            grouped_sections[title].append(section)

        # Create hierarchy
        for title, sections in grouped_sections.items():
            if len(sections) > 1:
                # Section appears in both sources
                hierarchy.append({
                    'title': sections[0]['title'],
                    'sources': [s['source'] for s in sections],
                    'recommended_source': 'combined',
                    'content_richness': max(s['content_count'] for s in sections)
                })
            else:
                # Section appears in only one source
                hierarchy.append({
                    'title': sections[0]['title'],
                    'sources': [sections[0]['source']],
                    'recommended_source': sections[0]['source'],
                    'content_richness': sections[0]['content_count']
                })

        return hierarchy

    def _extract_content_guidelines(self, llm_analysis: Dict) -> Dict[str, List[str]]:
        """Extract content guidelines from LLM analysis."""
        guidelines = {
            'pdf_best_practices': [],
            'html_best_practices': [],
            'combined_approaches': []
        }

        quality_assessment = llm_analysis.get('quality_assessment', {})

        # Extract PDF strengths as best practices
        pdf_strengths = quality_assessment.get('pdf_strengths', [])
        if isinstance(pdf_strengths, list):
            guidelines['pdf_best_practices'] = pdf_strengths
        elif isinstance(pdf_strengths, str):
            guidelines['pdf_best_practices'] = [pdf_strengths]

        # Extract HTML strengths as best practices
        html_strengths = quality_assessment.get('html_strengths', [])
        if isinstance(html_strengths, list):
            guidelines['html_best_practices'] = html_strengths
        elif isinstance(html_strengths, str):
            guidelines['html_best_practices'] = [html_strengths]

        # Extract template recommendations
        template_recs = llm_analysis.get('template_recommendations', [])
        if isinstance(template_recs, list):
            guidelines['combined_approaches'] = template_recs
        elif isinstance(template_recs, str):
            guidelines['combined_approaches'] = [template_recs]

        return guidelines

    def _define_quality_standards(self, pdf_content: Dict, html_content: Dict, llm_analysis: Dict) -> Dict[str, Any]:
        """Define quality standards for future templates."""
        standards = {
            'minimum_content_requirements': [],
            'validation_criteria': [],
            'completeness_metrics': {}
        }

        # Define minimum requirements based on content analysis
        pdf_sections = len(pdf_content.get('sections', []))
        html_sections = len(html_content.get('sections', []))

        standards['completeness_metrics'] = {
            'minimum_sections': min(pdf_sections, html_sections),
            'target_sections': max(pdf_sections, html_sections),
            'minimum_text_length': min(len(pdf_content.get('raw_text', '')), len(html_content.get('raw_text', ''))),
            'target_text_length': max(len(pdf_content.get('raw_text', '')), len(html_content.get('raw_text', '')))
        }

        # Add validation criteria
        standards['validation_criteria'] = [
            'All required sections must be present',
            'Technical specifications must be complete',
            'Safety information must be prominently featured',
            'Installation procedures must be step-by-step',
            'Troubleshooting section must be included'
        ]

        # Add minimum requirements
        standards['minimum_content_requirements'] = [
            'Product overview and specifications',
            'Safety warnings and requirements',
            'Installation procedures',
            'Configuration guidelines',
            'Troubleshooting information'
        ]

        return standards

    def save_template(self, template: Dict[str, Any], output_path: str):
        """Save the generated template."""
        try:
            with open(output_path, 'w') as f:
                json.dump(template, f, cls=EnhancedJSONEncoder, indent=2)
            print(f"✅ Template saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving template: {e}")

    def generate_template_summary(self, template: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the template."""
        summary_parts = [
            "🔧 SUPERSET TEMPLATE SUMMARY",
            "=" * 50,
            f"Device Family: {template['template_metadata']['device_family']}",
            f"Generated: {template['template_metadata']['generated_at']}",
            "",
            "📋 TEMPLATE STRUCTURE:",
            f"  Required Sections: {len(template['template_structure']['required_sections'])}",
            f"  Section Hierarchy: {len(template['template_structure']['section_hierarchy'])} levels",
            "",
            "📊 QUALITY STANDARDS:",
            f"  Minimum Sections: {template['quality_standards']['completeness_metrics']['minimum_sections']}",
            f"  Target Sections: {template['quality_standards']['completeness_metrics']['target_sections']}",
            "",
            "💡 CONTENT GUIDELINES:",
            f"  PDF Best Practices: {len(template['content_guidelines']['pdf_best_practices'])}",
            f"  HTML Best Practices: {len(template['content_guidelines']['html_best_practices'])}",
            f"  Combined Approaches: {len(template['content_guidelines']['combined_approaches'])}"
        ]

        return "\n".join(summary_parts)


def main():
    """Main function to generate superset template."""
    print("🚀 LLM Superset Template Generator")
    print("=" * 50)

    # File paths
    pdf_path = "b_C8500_HIG.pdf"
    html_path = "b_C8500.html"
    output_path = "c8500_superset_template.json"

    # Check if files exist
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return

    if not Path(html_path).exists():
        print(f"❌ HTML file not found: {html_path}")
        return

    # Initialize generator
    generator = LLMSupersetTemplateGenerator()

    # Extract content
    content_results = generator.extract_content(pdf_path, html_path)

    if content_results['extraction_errors']:
        print("❌ Extraction errors occurred:")
        for error in content_results['extraction_errors']:
            print(f"   - {error}")
        return

    # Analyze with LLM
    llm_analysis = generator.analyze_content_with_llm(
        content_results['pdf_content'],
        content_results['html_content']
    )

    # Generate superset template
    template = generator.generate_superset_template(
        content_results['pdf_content'],
        content_results['html_content'],
        llm_analysis
    )

    # Save template
    generator.save_template(template, output_path)

    # Print summary
    summary = generator.generate_template_summary(template)
    print(f"\n{summary}")

    print("\n🎯 Superset template generation complete!")
    print(f"   Template: {output_path}")
    print(f"   Use this template for future {template['template_metadata']['device_family']} documentation")


if __name__ == "__main__":
    main()
