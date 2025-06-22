#!/usr/bin/env python3
"""
Guide Analysis Script

Analyzes hardware documentation guides for content, structure, tone, and completeness.
Provides comprehensive comparison against reference guides or templates.

Usage:
    uv run analyze_guide.py \
        --guide path/to/guide.pdf \
        --reference path/to/reference_guide.json \
        --output_dir analysis_results

Features:
    - Content structure analysis
    - Tone and style assessment  
    - Completeness evaluation
    - Gap identification
    - Confidence scoring
    - Comparative analysis
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_doc_gen.input_processing.document_parser import parse_document
from ai_doc_gen.input_processing.structured_extractor import StructuredExtractor, ExtractedContent
from ai_doc_gen.agents.managing_agent import ManagingAgent
from ai_doc_gen.agents.review_agent import ReviewAgent
from ai_doc_gen.core.confidence_scoring import ConfidenceScorer
from ai_doc_gen.core.gap_analyzer import GapAnalyzer


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle complex objects safely."""
    
    def default(self, obj):
        # Handle enums
        if isinstance(obj, Enum):
            return obj.value
        
        # Handle objects with dict() method (Pydantic models)
        if hasattr(obj, 'dict'):
            try:
                return obj.dict()
            except:
                pass
        
        # Handle objects with as_dict() method
        if hasattr(obj, 'as_dict'):
            try:
                return obj.as_dict()
            except:
                pass
        
        # Handle objects with __dict__ but avoid recursion
        if hasattr(obj, '__dict__'):
            try:
                # Only include simple attributes to avoid recursion
                simple_attrs = {}
                for key, value in obj.__dict__.items():
                    if not key.startswith('_'):
                        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                            simple_attrs[key] = value
                        elif isinstance(value, Enum):
                            simple_attrs[key] = value.value
                        else:
                            simple_attrs[key] = str(value)
                return simple_attrs
            except:
                pass
        
        # Handle mappingproxy and similar objects
        if hasattr(obj, 'items'):
            try:
                return dict(obj)
            except:
                pass
        
        # Fallback to string representation
        return str(obj)


class GuideAnalyzer:
    """Comprehensive guide analysis tool."""
    
    def __init__(self):
        self.extractor = StructuredExtractor()
        self.managing_agent = ManagingAgent()
        self.review_agent = ReviewAgent()
        self.confidence_scorer = ConfidenceScorer()
        self.gap_analyzer = GapAnalyzer()
    
    def analyze_guide(
        self, 
        guide_path: str, 
        reference_path: Optional[str] = None,
        output_dir: str = "analysis_results"
    ) -> Dict[str, Any]:
        """Perform comprehensive guide analysis."""
        
        print(f"🔍 Analyzing guide: {guide_path}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Parse and extract content
        print("📄 Parsing document...")
        parsed_doc = parse_document(guide_path)
        extracted_content = self.extractor.extract_structured_content(parsed_doc)
        
        # Step 2: Analyze content structure
        print("🏗️  Analyzing content structure...")
        structure_analysis = self._analyze_content_structure(extracted_content)
        
        # Step 3: Analyze tone and style
        print("🎭 Analyzing tone and style...")
        tone_analysis = self._analyze_tone_and_style(extracted_content)
        
        # Step 4: Run agent analysis
        print("🤖 Running AI agent analysis...")
        agent_results = self.managing_agent.run(extracted_content)
        
        # Step 5: Review and audit
        print("🔍 Running review audit...")
        review_results = self.review_agent.run(extracted_content)
        
        # Step 6: Comparative analysis (if reference provided)
        comparison_results = {}
        if reference_path:
            print("📊 Running comparative analysis...")
            comparison_results = self._compare_with_reference(
                extracted_content, reference_path
            )
        
        # Step 7: Generate comprehensive report
        print("📋 Generating analysis report...")
        analysis_report = self._generate_analysis_report(
            guide_path=guide_path,
            reference_path=reference_path,
            parsed_doc=parsed_doc,
            extracted_content=extracted_content,
            structure_analysis=structure_analysis,
            tone_analysis=tone_analysis,
            agent_results=agent_results,
            review_results=review_results,
            comparison_results=comparison_results
        )
        
        # Save results
        self._save_analysis_results(analysis_report, output_dir)
        
        print(f"✅ Analysis complete! Results saved to: {output_dir}")
        return analysis_report
    
    def _analyze_content_structure(self, content: List[ExtractedContent]) -> Dict[str, Any]:
        """Analyze the structure and organization of content."""
        
        # Content type distribution
        content_types = {}
        for item in content:
            content_type = item.content_type.value
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Section analysis
        sections = {}
        for item in content:
            section = item.source_section
            if section not in sections:
                sections[section] = {
                    'count': 0,
                    'types': set(),
                    'avg_confidence': 0.0
                }
            sections[section]['count'] += 1
            sections[section]['types'].add(item.content_type.value)
        
        # Calculate average confidence per section
        for section in sections:
            section_items = [item for item in content if item.source_section == section]
            avg_confidence = sum(item.confidence for item in section_items) / len(section_items)
            sections[section]['avg_confidence'] = avg_confidence
            sections[section]['types'] = list(sections[section]['types'])
        
        return {
            'total_items': len(content),
            'content_type_distribution': content_types,
            'section_analysis': sections,
            'structure_score': self._calculate_structure_score(content)
        }
    
    def _analyze_tone_and_style(self, content: List[ExtractedContent]) -> Dict[str, Any]:
        """Analyze the tone and writing style of the guide."""
        
        # Tone indicators
        tone_indicators = {
            'formal': 0,
            'technical': 0,
            'instructional': 0,
            'cautionary': 0,
            'informative': 0
        }
        
        # Style metrics
        avg_sentence_length = 0
        total_sentences = 0
        technical_terms = set()
        
        for item in content:
            text = item.content.lower()
            
            # Count tone indicators
            if any(word in text for word in ['shall', 'must', 'required', 'mandatory']):
                tone_indicators['formal'] += 1
            if any(word in text for word in ['specification', 'technical', 'parameter']):
                tone_indicators['technical'] += 1
            if any(word in text for word in ['step', 'procedure', 'instruction']):
                tone_indicators['instructional'] += 1
            if any(word in text for word in ['warning', 'caution', 'danger']):
                tone_indicators['cautionary'] += 1
            if any(word in text for word in ['note', 'information', 'details']):
                tone_indicators['informative'] += 1
            
            # Analyze sentence structure
            sentences = text.split('.')
            total_sentences += len(sentences)
            avg_sentence_length += sum(len(s.split()) for s in sentences)
            
            # Extract technical terms (simplified)
            words = text.split()
            for word in words:
                if len(word) > 8 and word.isalpha():
                    technical_terms.add(word)
        
        avg_sentence_length = avg_sentence_length / max(total_sentences, 1)
        
        return {
            'tone_indicators': tone_indicators,
            'avg_sentence_length': avg_sentence_length,
            'technical_terms_count': len(technical_terms),
            'technical_terms_sample': list(technical_terms)[:10],
            'style_score': self._calculate_style_score(tone_indicators, avg_sentence_length)
        }
    
    def _compare_with_reference(
        self, 
        content: List[ExtractedContent], 
        reference_path: str
    ) -> Dict[str, Any]:
        """Compare guide content with reference guide."""
        
        try:
            with open(reference_path, 'r') as f:
                reference_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load reference file: {e}")
            return {'error': f'Could not load reference: {e}'}
        
        # Extract reference content types
        reference_types = set()
        if 'content_types' in reference_data:
            reference_types = set(reference_data['content_types'].keys())
        
        # Compare content types
        current_types = {item.content_type.value for item in content}
        missing_types = reference_types - current_types
        extra_types = current_types - reference_types
        common_types = reference_types & current_types
        
        # Coverage analysis
        coverage_percentage = len(common_types) / len(reference_types) * 100 if reference_types else 0
        
        return {
            'reference_types': list(reference_types),
            'current_types': list(current_types),
            'missing_types': list(missing_types),
            'extra_types': list(extra_types),
            'common_types': list(common_types),
            'coverage_percentage': coverage_percentage,
            'completeness_score': coverage_percentage / 100
        }
    
    def _calculate_structure_score(self, content: List[ExtractedContent]) -> float:
        """Calculate a score for content structure quality."""
        if not content:
            return 0.0
        
        # Factors: content type diversity, section organization, confidence distribution
        content_types = len({item.content_type.value for item in content})
        sections = len({item.source_section for item in content})
        avg_confidence = sum(item.confidence for item in content) / len(content)
        
        # Normalize scores
        type_score = min(content_types / 10, 1.0)  # Assume 10 types is good
        section_score = min(sections / 5, 1.0)     # Assume 5 sections is good
        confidence_score = avg_confidence
        
        return (type_score + section_score + confidence_score) / 3
    
    def _calculate_style_score(self, tone_indicators: Dict[str, int], avg_sentence_length: float) -> float:
        """Calculate a score for writing style quality."""
        
        # Prefer balanced tone indicators
        total_indicators = sum(tone_indicators.values())
        if total_indicators == 0:
            return 0.0
        
        # Balance score (prefer variety)
        max_indicator = max(tone_indicators.values())
        balance_score = 1.0 - (max_indicator / total_indicators)
        
        # Sentence length score (prefer moderate length)
        length_score = 1.0 - abs(avg_sentence_length - 15) / 15  # 15 words is ideal
        
        return (balance_score + length_score) / 2
    
    def _generate_analysis_report(self, **kwargs) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        
        return {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'guide_path': kwargs['guide_path'],
                'reference_path': kwargs['reference_path'],
                'analysis_version': '1.0'
            },
            'document_info': {
                'filename': os.path.basename(kwargs['guide_path']),
                'total_sections': len(kwargs['parsed_doc'].sections),
                'total_content_items': len(kwargs['extracted_content']),
                'raw_text_length': len(kwargs['parsed_doc'].raw_text)
            },
            'structure_analysis': kwargs['structure_analysis'],
            'tone_analysis': kwargs['tone_analysis'],
            'agent_analysis': kwargs['agent_results'],
            'review_analysis': kwargs['review_results'],
            'comparison_analysis': kwargs['comparison_results'],
            'overall_scores': {
                'structure_score': kwargs['structure_analysis']['structure_score'],
                'style_score': kwargs['tone_analysis']['style_score'],
                'confidence_score': sum(item.confidence for item in kwargs['extracted_content']) / len(kwargs['extracted_content']),
                'completeness_score': kwargs['comparison_results'].get('completeness_score', 0.0)
            },
            'recommendations': self._generate_recommendations(kwargs)
        }
    
    def _generate_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        
        recommendations = []
        
        # Structure recommendations
        structure_score = analysis_data['structure_analysis']['structure_score']
        if structure_score < 0.7:
            recommendations.append("Consider improving content organization and structure")
        
        # Style recommendations
        style_score = analysis_data['tone_analysis']['style_score']
        if style_score < 0.7:
            recommendations.append("Review writing style for consistency and clarity")
        
        # Content type recommendations
        content_types = analysis_data['structure_analysis']['content_type_distribution']
        if 'warning' not in content_types:
            recommendations.append("Consider adding safety warnings and cautions")
        if 'requirement' not in content_types:
            recommendations.append("Consider adding clear requirements and prerequisites")
        
        # Confidence recommendations
        low_confidence_items = [
            item for item in analysis_data['extracted_content'] 
            if item.confidence < 0.7
        ]
        if low_confidence_items:
            recommendations.append(f"Review {len(low_confidence_items)} low-confidence content items")
        
        # Comparison recommendations
        if analysis_data['comparison_results']:
            coverage = analysis_data['comparison_results'].get('coverage_percentage', 0)
            if coverage < 80:
                recommendations.append(f"Guide covers only {coverage:.1f}% of reference content types")
        
        return recommendations
    
    def _save_analysis_results(self, report: Dict[str, Any], output_dir: str):
        """Save analysis results to files."""
        
        # Save full report using custom encoder
        report_path = os.path.join(output_dir, 'analysis_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, cls=CustomJSONEncoder)
        
        # Save summary
        summary_path = os.path.join(output_dir, 'analysis_summary.txt')
        with open(summary_path, 'w') as f:
            f.write("GUIDE ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Guide: {report['document_info']['filename']}\n")
            f.write(f"Analysis Date: {report['analysis_metadata']['timestamp']}\n\n")
            
            f.write("OVERALL SCORES:\n")
            f.write("-" * 20 + "\n")
            for score_name, score_value in report['overall_scores'].items():
                f.write(f"{score_name.replace('_', ' ').title()}: {score_value:.2f}\n")
            f.write("\n")
            
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 20 + "\n")
            for rec in report['recommendations']:
                f.write(f"• {rec}\n")
            f.write("\n")
            
            f.write("CONTENT TYPE DISTRIBUTION:\n")
            f.write("-" * 30 + "\n")
            for content_type, count in report['structure_analysis']['content_type_distribution'].items():
                f.write(f"{content_type}: {count}\n")
        
        print(f"📄 Full report: {report_path}")
        print(f"📋 Summary: {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze hardware documentation guides")
    parser.add_argument("--guide", required=True, help="Path to guide PDF/DOCX to analyze")
    parser.add_argument("--reference", help="Path to reference guide JSON for comparison")
    parser.add_argument("--output_dir", default="analysis_results", help="Output directory for results")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.guide):
        print(f"Error: Guide file not found: {args.guide}")
        sys.exit(1)
    
    if args.reference and not os.path.exists(args.reference):
        print(f"Error: Reference file not found: {args.reference}")
        sys.exit(1)
    
    # Run analysis
    analyzer = GuideAnalyzer()
    try:
        results = analyzer.analyze_guide(
            guide_path=args.guide,
            reference_path=args.reference,
            output_dir=args.output_dir
        )
        
        # Print key findings
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE - KEY FINDINGS")
        print("="*60)
        
        scores = results['overall_scores']
        print(f"📊 Structure Score: {scores['structure_score']:.2f}")
        print(f"🎭 Style Score: {scores['style_score']:.2f}")
        print(f"🎯 Confidence Score: {scores['confidence_score']:.2f}")
        print(f"📈 Completeness Score: {scores['completeness_score']:.2f}")
        
        print(f"\n📋 Content Items: {results['document_info']['total_content_items']}")
        print(f"🏗️  Sections: {results['document_info']['total_sections']}")
        
        if results['recommendations']:
            print("\n💡 Top Recommendations:")
            for rec in results['recommendations'][:3]:
                print(f"   • {rec}")
        
        print(f"\n📁 Results saved to: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 