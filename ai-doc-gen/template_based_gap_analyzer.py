#!/usr/bin/env python3
"""
Template-Based Gap Analyzer
Uses the superset template as ground truth to analyze new documents and identify gaps.
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


class TemplateBasedGapAnalyzer:
    """Analyzes new documents against a superset template to identify gaps."""

    def __init__(self, template_path: str):
        self.template_path = template_path
        self.template = self._load_template(template_path)
        self.pdf_parser = PDFParser()
        self.html_parser = HTMLParser()
        self.docx_parser = DOCXParser()

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

    def analyze_document_against_template(self, document_path: str) -> Dict[str, Any]:
        """Analyze a new document against the superset template."""
        print(f"🔍 Analyzing document against template: {document_path}")

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

        # Analyze against template
        analysis = {
            'document_info': {
                'path': document_path,
                'type': doc_type,
                'sections': len(parsed_doc.sections),
                'text_length': len(parsed_doc.raw_text),
                'title': parsed_doc.title
            },
            'template_comparison': self._compare_against_template(parsed_doc),
            'gap_analysis': self._identify_gaps(parsed_doc),
            'quality_assessment': self._assess_quality(parsed_doc),
            'recommendations': []
        }

        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)

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

    def _compare_against_template(self, parsed_doc: ParsedDocument) -> Dict[str, Any]:
        """Compare document sections against template requirements."""
        template_sections = self.template.get('template_structure', {}).get('section_hierarchy', [])
        required_sections = self.template.get('template_structure', {}).get('required_sections', [])
        quality_standards = self.template.get('quality_standards', {})

        # Extract document section titles
        doc_sections = [s.get('heading', '') for s in parsed_doc.sections if s.get('heading')]

        # Find matches with template sections
        matches = []
        missing_sections = []
        extra_sections = []

        for template_section in template_sections:
            template_title = template_section.get('title', '')
            best_match = self._find_best_match(template_title, doc_sections)

            if best_match and best_match['similarity'] > 0.6:  # 60% similarity threshold
                matches.append({
                    'template_section': template_title,
                    'document_section': best_match['title'],
                    'similarity': best_match['similarity'],
                    'template_source': template_section.get('recommended_source', 'unknown'),
                    'content_richness': template_section.get('content_richness', 0)
                })
            else:
                missing_sections.append({
                    'template_section': template_title,
                    'template_source': template_section.get('recommended_source', 'unknown'),
                    'importance': 'high' if template_title.lower() in [s.lower() for s in required_sections] else 'medium'
                })

        # Find sections in document not in template
        template_titles = [s.get('title', '') for s in template_sections]
        for doc_section in doc_sections:
            best_match = self._find_best_match(doc_section, template_titles)
            if not best_match:  # No match found
                extra_sections.append(doc_section)

        return {
            'matches': matches,
            'missing_sections': missing_sections,
            'extra_sections': extra_sections,
            'coverage_percentage': len(matches) / len(template_sections) * 100 if template_sections else 0,
            'required_sections_covered': len([m for m in matches if m['template_section'].lower() in [s.lower() for s in required_sections]])
        }

    def _find_best_match(self, target: str, candidates: List[str]) -> Optional[Dict[str, Any]]:
        """Find the best matching section title."""
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

        return best_match if best_similarity > 0.3 else None  # 30% minimum similarity

    def _identify_gaps(self, parsed_doc: ParsedDocument) -> Dict[str, Any]:
        """Identify specific content gaps."""
        template_guidelines = self.template.get('content_guidelines', {})
        quality_standards = self.template.get('quality_standards', {})

        gaps = {
            'missing_required_sections': [],
            'content_depth_gaps': [],
            'quality_gaps': [],
            'structural_gaps': []
        }

        # Check for missing required sections
        required_sections = quality_standards.get('minimum_content_requirements', [])
        doc_sections = [s.get('heading', '').lower() for s in parsed_doc.sections if s.get('heading')]

        for required in required_sections:
            if not any(required.lower() in section for section in doc_sections):
                gaps['missing_required_sections'].append(required)

        # Check content depth
        completeness_metrics = quality_standards.get('completeness_metrics', {})
        target_sections = completeness_metrics.get('target_sections', 0)
        target_text_length = completeness_metrics.get('target_text_length', 0)

        if len(parsed_doc.sections) < target_sections * 0.8:  # 80% of target
            gaps['content_depth_gaps'].append(f"Document has {len(parsed_doc.sections)} sections, target is {target_sections}")

        if len(parsed_doc.raw_text) < target_text_length * 0.8:  # 80% of target
            gaps['content_depth_gaps'].append(f"Document has {len(parsed_doc.raw_text)} characters, target is {target_text_length}")

        # Check structural gaps
        validation_criteria = quality_standards.get('validation_criteria', [])
        for criterion in validation_criteria:
            if 'step-by-step' in criterion.lower() and not self._has_step_by_step_content(parsed_doc):
                gaps['structural_gaps'].append("Missing step-by-step procedures")
            elif 'safety' in criterion.lower() and not self._has_safety_content(parsed_doc):
                gaps['structural_gaps'].append("Missing prominent safety information")

        return gaps

    def _has_step_by_step_content(self, parsed_doc: ParsedDocument) -> bool:
        """Check if document has step-by-step content."""
        step_keywords = ['step', 'procedure', 'instruction', 'guide']
        text = parsed_doc.raw_text.lower()
        return any(keyword in text for keyword in step_keywords)

    def _has_safety_content(self, parsed_doc: ParsedDocument) -> bool:
        """Check if document has safety content."""
        safety_keywords = ['safety', 'warning', 'caution', 'danger', 'precaution']
        text = parsed_doc.raw_text.lower()
        return any(keyword in text for keyword in safety_keywords)

    def _assess_quality(self, parsed_doc: ParsedDocument) -> Dict[str, Any]:
        """Assess document quality against template standards."""
        quality_standards = self.template.get('quality_standards', {})
        completeness_metrics = quality_standards.get('completeness_metrics', {})

        # Calculate quality scores
        section_score = len(parsed_doc.sections) / completeness_metrics.get('target_sections', 1) * 100
        text_score = len(parsed_doc.raw_text) / completeness_metrics.get('target_text_length', 1) * 100

        # Overall quality score
        overall_score = (section_score + text_score) / 2

        return {
            'overall_score': min(overall_score, 100),  # Cap at 100%
            'section_completeness': min(section_score, 100),
            'text_completeness': min(text_score, 100),
            'quality_level': self._get_quality_level(overall_score),
            'meets_minimum_standards': overall_score >= 60  # 60% threshold
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

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Coverage recommendations
        coverage = analysis['template_comparison']['coverage_percentage']
        if coverage < 50:
            recommendations.append(f"Low template coverage ({coverage:.1f}%) - consider adding more sections from the template")
        elif coverage < 80:
            recommendations.append(f"Moderate template coverage ({coverage:.1f}%) - review missing sections")

        # Missing required sections
        missing_required = analysis['gap_analysis']['missing_required_sections']
        if missing_required:
            recommendations.append(f"Missing required sections: {', '.join(missing_required[:3])}")

        # Quality recommendations
        quality = analysis['quality_assessment']
        if quality['overall_score'] < 70:
            recommendations.append(f"Quality score is {quality['overall_score']:.1f}% - needs improvement")

        # Content depth recommendations
        content_gaps = analysis['gap_analysis']['content_depth_gaps']
        if content_gaps:
            recommendations.append("Content depth gaps detected - consider expanding sections")

        # Structural recommendations
        structural_gaps = analysis['gap_analysis']['structural_gaps']
        if structural_gaps:
            recommendations.append(f"Structural issues: {', '.join(structural_gaps)}")

        if not recommendations:
            recommendations.append("Document meets template standards well")

        return recommendations

    def print_analysis_summary(self, analysis: Dict[str, Any]):
        """Print a human-readable analysis summary."""
        print("\n" + "="*60)
        print("📊 TEMPLATE-BASED GAP ANALYSIS SUMMARY")
        print("="*60)

        # Document info
        doc_info = analysis['document_info']
        print("\n📄 DOCUMENT INFO:")
        print(f"   File: {doc_info['path']}")
        print(f"   Type: {doc_info['type']}")
        print(f"   Sections: {doc_info['sections']}")
        print(f"   Text Length: {doc_info['text_length']:,} characters")

        # Template comparison
        comparison = analysis['template_comparison']
        print("\n🔄 TEMPLATE COMPARISON:")
        print(f"   Coverage: {comparison['coverage_percentage']:.1f}%")
        print(f"   Matches: {len(comparison['matches'])}")
        print(f"   Missing: {len(comparison['missing_sections'])}")
        print(f"   Extra: {len(comparison['extra_sections'])}")

        # Quality assessment
        quality = analysis['quality_assessment']
        print("\n📊 QUALITY ASSESSMENT:")
        print(f"   Overall Score: {quality['overall_score']:.1f}% ({quality['quality_level']})")
        print(f"   Section Completeness: {quality['section_completeness']:.1f}%")
        print(f"   Text Completeness: {quality['text_completeness']:.1f}%")
        print(f"   Meets Standards: {'✅' if quality['meets_minimum_standards'] else '❌'}")

        # Gap analysis
        gaps = analysis['gap_analysis']
        print("\n🔍 GAP ANALYSIS:")
        print(f"   Missing Required: {len(gaps['missing_required_sections'])}")
        print(f"   Content Depth Gaps: {len(gaps['content_depth_gaps'])}")
        print(f"   Quality Gaps: {len(gaps['quality_gaps'])}")
        print(f"   Structural Gaps: {len(gaps['structural_gaps'])}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"   {i}. {rec}")

        print("\n" + "="*60)

    def save_analysis(self, analysis: Dict[str, Any], output_path: str):
        """Save analysis results to JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(analysis, f, cls=EnhancedJSONEncoder, indent=2)
            print(f"✅ Analysis saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")


def main():
    """Main function to run template-based gap analysis."""
    print("🔍 Template-Based Gap Analyzer")
    print("=" * 50)

    # Template path
    template_path = "c8500_superset_template.json"
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        print("   Run llm_superset_template_generator.py first to create the template")
        return

    # Document to analyze (can be DOCX, PDF, or HTML)
    document_path = "functional_spec.docx"  # Change this to your document
    if not Path(document_path).exists():
        print(f"❌ Document not found: {document_path}")
        print("   Please specify a valid document path")
        return

    # Initialize analyzer
    analyzer = TemplateBasedGapAnalyzer(template_path)

    # Run analysis
    print(f"🔍 Analyzing {document_path} against template...")
    analysis = analyzer.analyze_document_against_template(document_path)

    if 'error' in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return

    # Print summary
    analyzer.print_analysis_summary(analysis)

    # Save results
    output_path = f"gap_analysis_{Path(document_path).stem}.json"
    analyzer.save_analysis(analysis, output_path)

    print("\n🎯 Gap analysis complete!")
    print(f"   Results: {output_path}")
    print("   Use these results to improve the document against the template")


if __name__ == "__main__":
    main()
