#!/usr/bin/env python3
"""
LLM-Enhanced Section Matcher
Uses LLM to intelligently match document sections to template sections using semantic understanding.
"""

import difflib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ai_doc_gen.input_processing.document_parser import (
    DOCXParser,
    HTMLParser,
    ParsedDocument,
    PDFParser,
)
from src.ai_doc_gen.utils.serialization import EnhancedJSONEncoder


class LLMEnhancedMatcher:
    """Uses LLM to enhance section matching with semantic understanding."""

    def __init__(self, template_path: str, api_key: Optional[str] = None):
        self.template_path = template_path
        self.template = self._load_template(template_path)
        self.pdf_parser = PDFParser()
        self.html_parser = HTMLParser()
        self.docx_parser = DOCXParser()
        self.client = None

        if api_key:
            import openai
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
        else:
            # Try to get from environment
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                import openai
                self.client = openai.OpenAI(api_key=api_key)
            else:
                print("⚠️  No OpenAI API key found. LLM matching will be disabled.")

    def _load_template(self, template_path: str) -> Dict[str, Any]:
        """Load the superset template."""
        try:
            with open(template_path) as f:
                template = json.load(f)
            print(f"✅ Loaded template: {template['template_metadata']['device_family']}")
            return template
        except Exception as e:
            print(f"❌ Error loading template: {e}")
            return {}

    def analyze_document_with_llm_matching(self, document_path: str) -> Dict[str, Any]:
        """Analyze document with LLM-enhanced section matching."""
        print(f"🔍 Analyzing document with LLM matching: {document_path}")

        # Determine document type and parse
        doc_type = self._get_document_type(document_path)
        parser = self._get_parser(doc_type)

        if not parser:
            return {'error': f'Unsupported document type: {doc_type}'}

        # Parse the document
        try:
            parsed_doc = parser.parse(document_path)
            print(f"   ✅ Parsed: {len(parsed_doc.sections)} sections")
        except Exception as e:
            return {'error': f'Parsing failed: {e}'}

        # Get template sections
        template_sections = self.template.get('template_structure', {}).get('section_hierarchy', [])

        # Perform LLM-enhanced matching
        llm_matches = self._llm_match_sections(parsed_doc.sections, template_sections)

        # Perform traditional matching for comparison
        traditional_matches = self._traditional_match_sections(parsed_doc.sections, template_sections)

        # Analyze results
        analysis = {
            'document_info': {
                'path': document_path,
                'type': doc_type,
                'sections': len(parsed_doc.sections),
                'text_length': len(parsed_doc.raw_text),
                'title': parsed_doc.title
            },
            'llm_matching': llm_matches,
            'traditional_matching': traditional_matches,
            'comparison': self._compare_matching_methods(llm_matches, traditional_matches),
            'quality_assessment': self._assess_quality_with_llm(parsed_doc, llm_matches),
            'recommendations': []
        }

        # Generate recommendations
        analysis['recommendations'] = self._generate_llm_recommendations(analysis)

        return analysis

    def _get_document_type(self, file_path: str) -> str:
        """Determine document type from file extension."""
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return 'PDF'
        elif ext == '.html' or ext == '.htm':
            return 'HTML'
        elif ext == '.docx':
            return 'DOCX'
        else:
            return 'UNKNOWN'

    def _get_parser(self, doc_type: str):
        """Get appropriate parser for document type."""
        parsers = {
            'PDF': self.pdf_parser,
            'HTML': self.html_parser,
            'DOCX': self.docx_parser
        }
        return parsers.get(doc_type)

    def _llm_match_sections(self, doc_sections: List[Dict], template_sections: List[Dict]) -> Dict[str, Any]:
        """Use LLM to semantically match document sections to template sections."""
        if not self.client:
            print("   ⚠️  LLM client not available - using traditional matching only")
            return self._traditional_match_sections(doc_sections, template_sections)

        print("   🤖 Using LLM for semantic section matching...")

        # Prepare section data for LLM
        doc_section_data = []
        for i, section in enumerate(doc_sections[:20]):  # Limit to first 20 for efficiency
            heading = section.get('heading', f'Section {i+1}')
            content = section.get('content', [])
            content_text = ' '.join([str(c) for c in content[:3]])[:200]  # First 3 content items, 200 chars

            doc_section_data.append({
                'id': i,
                'heading': heading,
                'content_preview': content_text,
                'content_count': len(content)
            })

        template_section_data = []
        for i, section in enumerate(template_sections):
            template_section_data.append({
                'id': i,
                'title': section.get('title', ''),
                'recommended_source': section.get('recommended_source', 'unknown'),
                'content_richness': section.get('content_richness', 0)
            })

        # Create LLM prompt for semantic matching
        prompt = self._create_matching_prompt(doc_section_data, template_section_data)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent matching
                max_tokens=2000
            )

            llm_response = response.choices[0].message.content
            matches = self._parse_llm_matching_response(llm_response, doc_section_data, template_section_data)

            print(f"   ✅ LLM matching complete: {len(matches)} semantic matches found")
            return {
                'matches': matches,
                'coverage_percentage': len(matches) / len(template_sections) * 100 if template_sections else 0,
                'llm_response': llm_response
            }

        except Exception as e:
            print(f"   ❌ LLM matching failed: {e}")
            return self._traditional_match_sections(doc_sections, template_sections)

    def _create_matching_prompt(self, doc_sections: List[Dict], template_sections: List[Dict]) -> str:
        """Create LLM prompt for semantic section matching."""

        doc_sections_text = "\n".join([
            f"Doc Section {s['id']}: '{s['heading']}' (Content: {s['content_preview']}...)"
            for s in doc_sections
        ])

        template_sections_text = "\n".join([
            f"Template Section {s['id']}: '{s['title']}' (Source: {s['recommended_source']})"
            for s in template_sections
        ])

        prompt = f"""
You are an expert technical documentation analyst. Your task is to match document sections to template sections based on semantic similarity and content purpose.

DOCUMENT SECTIONS:
{doc_sections_text}

TEMPLATE SECTIONS:
{template_sections_text}

For each document section, identify which template section(s) it best matches semantically. Consider:
- Content purpose and intent
- Technical domain (installation, safety, specifications, etc.)
- Content type (procedural, descriptive, requirements, etc.)
- Even if titles don't match exactly, match based on what the content actually covers

Provide your response as a JSON array of matches with this structure:
[
  {{
    "doc_section_id": 0,
    "template_section_id": 5,
    "confidence": 0.9,
    "reasoning": "Both cover installation procedures and safety requirements"
  }}
]

Only include matches where confidence > 0.6. If a document section doesn't clearly match any template section, don't include it.
"""

        return prompt

    def _parse_llm_matching_response(self, response: str, doc_sections: List[Dict], template_sections: List[Dict]) -> List[Dict]:
        """Parse LLM response into structured matches."""
        try:
            # Extract JSON from response
            if '{' in response and '}' in response:
                start = response.find('[')
                end = response.rfind(']') + 1
                if start != -1 and end != -1:
                    json_str = response[start:end]
                    matches = json.loads(json_str)

                    # Enhance matches with section details
                    enhanced_matches = []
                    for match in matches:
                        doc_id = match.get('doc_section_id')
                        template_id = match.get('template_section_id')

                        if doc_id < len(doc_sections) and template_id < len(template_sections):
                            enhanced_matches.append({
                                'doc_section': doc_sections[doc_id]['heading'],
                                'template_section': template_sections[template_id]['title'],
                                'confidence': match.get('confidence', 0.0),
                                'reasoning': match.get('reasoning', ''),
                                'template_source': template_sections[template_id]['recommended_source']
                            })

                    return enhanced_matches

            return []

        except Exception as e:
            print(f"   ⚠️  Error parsing LLM response: {e}")
            return []

    def _traditional_match_sections(self, doc_sections: List[Dict], template_sections: List[Dict]) -> Dict[str, Any]:
        """Traditional string-based section matching."""
        doc_titles = [s.get('heading', '') for s in doc_sections if s.get('heading')]
        template_titles = [s.get('title', '') for s in template_sections]

        matches = []
        for template_section in template_sections:
            template_title = template_section.get('title', '')
            best_match = self._find_best_match(template_title, doc_titles)

            if best_match and best_match['similarity'] > 0.6:
                matches.append({
                    'doc_section': best_match['title'],
                    'template_section': template_title,
                    'confidence': best_match['similarity'],
                    'reasoning': f'String similarity: {best_match["similarity"]:.2f}',
                    'template_source': template_section.get('recommended_source', 'unknown')
                })

        return {
            'matches': matches,
            'coverage_percentage': len(matches) / len(template_sections) * 100 if template_sections else 0
        }

    def _find_best_match(self, target: str, candidates: List[str]) -> Optional[Dict[str, Any]]:
        """Find the best matching section title using string similarity."""
        if not candidates:
            return None

        best_match = None
        best_similarity = 0

        for candidate in candidates:
            similarity = difflib.SequenceMatcher(None, target.lower(), candidate.lower()).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'title': candidate,
                    'similarity': similarity
                }

        return best_match if best_similarity > 0.3 else None

    def _compare_matching_methods(self, llm_matches: Dict[str, Any], traditional_matches: Dict[str, Any]) -> Dict[str, Any]:
        """Compare LLM vs traditional matching results."""
        llm_coverage = llm_matches.get('coverage_percentage', 0)
        traditional_coverage = traditional_matches.get('coverage_percentage', 0)

        improvement = llm_coverage - traditional_coverage

        return {
            'llm_coverage': llm_coverage,
            'traditional_coverage': traditional_coverage,
            'improvement': improvement,
            'improvement_percentage': (improvement / traditional_coverage * 100) if traditional_coverage > 0 else 0,
            'llm_matches_count': len(llm_matches.get('matches', [])),
            'traditional_matches_count': len(traditional_matches.get('matches', []))
        }

    def _assess_quality_with_llm(self, parsed_doc: ParsedDocument, llm_matches: Dict[str, Any]) -> Dict[str, Any]:
        """Assess document quality using LLM matching results."""
        quality_standards = self.template.get('quality_standards', {})
        completeness_metrics = quality_standards.get('completeness_metrics', {})

        # Calculate quality scores based on LLM matches
        llm_coverage = llm_matches.get('coverage_percentage', 0)
        target_sections = completeness_metrics.get('target_sections', 0)
        target_text_length = completeness_metrics.get('target_text_length', 0)

        section_score = len(parsed_doc.sections) / target_sections * 100 if target_sections > 0 else 0
        text_score = len(parsed_doc.raw_text) / target_text_length * 100 if target_text_length > 0 else 0

        # Weight the overall score to consider LLM coverage
        overall_score = (llm_coverage * 0.4 + section_score * 0.3 + text_score * 0.3)

        return {
            'overall_score': min(overall_score, 100),
            'llm_coverage_score': llm_coverage,
            'section_completeness': min(section_score, 100),
            'text_completeness': min(text_score, 100),
            'quality_level': self._get_quality_level(overall_score),
            'meets_minimum_standards': overall_score >= 60
        }

    def _get_quality_level(self, score: float) -> str:
        """Convert score to quality level."""
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Fair'
        elif score >= 60:
            return 'Acceptable'
        else:
            return 'Poor'

    def _generate_llm_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on LLM matching results."""
        recommendations = []

        comparison = analysis['comparison']
        llm_coverage = comparison.get('llm_coverage', 0)
        improvement = comparison.get('improvement', 0)

        # Coverage recommendations
        if llm_coverage < 30:
            recommendations.append(f"Low semantic coverage ({llm_coverage:.1f}%) - document may need structural improvements")
        elif llm_coverage < 60:
            recommendations.append(f"Moderate semantic coverage ({llm_coverage:.1f}%) - consider adding missing content areas")

        # LLM improvement recommendations
        if improvement > 10:
            recommendations.append(f"LLM matching improved coverage by {improvement:.1f}% over traditional matching")
        elif improvement < 0:
            recommendations.append("LLM matching reduced coverage - may indicate template needs refinement")

        # Quality recommendations
        quality = analysis['quality_assessment']
        if quality['overall_score'] < 70:
            recommendations.append(f"Overall quality score is {quality['overall_score']:.1f}% - needs improvement")

        if not recommendations:
            recommendations.append("Document shows good semantic alignment with template")

        return recommendations

    def print_enhanced_analysis(self, analysis: Dict[str, Any]):
        """Print enhanced analysis with LLM matching results."""
        print("\n" + "="*80)
        print("🤖 LLM-ENHANCED SECTION MATCHING ANALYSIS")
        print("="*80)

        # Document info
        doc_info = analysis['document_info']
        print("\n📄 DOCUMENT INFO:")
        print(f"   File: {doc_info['path']}")
        print(f"   Type: {doc_info['type']}")
        print(f"   Sections: {doc_info['sections']}")
        print(f"   Text Length: {doc_info['text_length']:,} characters")

        # Matching comparison
        comparison = analysis['comparison']
        print("\n🔄 MATCHING COMPARISON:")
        print(f"   Traditional Coverage: {comparison['traditional_coverage']:.1f}% ({comparison['traditional_matches_count']} matches)")
        print(f"   LLM Coverage: {comparison['llm_coverage']:.1f}% ({comparison['llm_matches_count']} matches)")
        print(f"   Improvement: {comparison['improvement']:.1f}% ({comparison['improvement_percentage']:.1f}% relative)")

        # LLM matches details
        llm_matches = analysis['llm_matching'].get('matches', [])
        if llm_matches:
            print("\n🤖 LLM SEMANTIC MATCHES (Top 5):")
            for i, match in enumerate(llm_matches[:5], 1):
                print(f"   {i}. '{match['doc_section']}' → '{match['template_section']}'")
                print(f"      Confidence: {match['confidence']:.2f}, Reason: {match['reasoning'][:60]}...")

        # Quality assessment
        quality = analysis['quality_assessment']
        print("\n📊 ENHANCED QUALITY ASSESSMENT:")
        print(f"   Overall Score: {quality['overall_score']:.1f}% ({quality['quality_level']})")
        print(f"   LLM Coverage Score: {quality['llm_coverage_score']:.1f}%")
        print(f"   Section Completeness: {quality['section_completeness']:.1f}%")
        print(f"   Text Completeness: {quality['text_completeness']:.1f}%")
        print(f"   Meets Standards: {'✅' if quality['meets_minimum_standards'] else '❌'}")

        # Recommendations
        print("\n💡 LLM-ENHANCED RECOMMENDATIONS:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"   {i}. {rec}")

        print("\n" + "="*80)

    def save_enhanced_analysis(self, analysis: Dict[str, Any], output_path: str):
        """Save enhanced analysis results."""
        try:
            with open(output_path, 'w') as f:
                json.dump(analysis, f, cls=EnhancedJSONEncoder, indent=2)
            print(f"✅ Enhanced analysis saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")


def main():
    """Main function to test LLM-enhanced matching."""
    print("🚀 LLM-Enhanced Section Matcher")
    print("=" * 50)

    # Template path
    template_path = "c8500_superset_template.json"
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        print("   Run llm_superset_template_generator.py first to create the template")
        return

    # Document to test
    document_path = "functional_spec.docx"
    if not Path(document_path).exists():
        print(f"❌ Document not found: {document_path}")
        return

    # Initialize enhanced matcher
    matcher = LLMEnhancedMatcher(template_path)

    # Run enhanced analysis
    analysis = matcher.analyze_document_with_llm_matching(document_path)

    if 'error' in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return

    # Print results
    matcher.print_enhanced_analysis(analysis)

    # Save results
    output_path = f"llm_enhanced_analysis_{Path(document_path).stem}.json"
    matcher.save_enhanced_analysis(analysis, output_path)

    print("\n🎯 LLM-enhanced analysis complete!")
    print(f"   Results: {output_path}")
    print("   Compare with traditional matching to see the improvement")


if __name__ == "__main__":
    main()
