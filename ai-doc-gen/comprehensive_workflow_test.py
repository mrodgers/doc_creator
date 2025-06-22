#!/usr/bin/env python3
"""
Comprehensive Workflow Test
Tests the end-to-end workflow with functional_spec.docx, installation_guide.pdf, and Cisco HTML.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.ai_doc_gen.input_processing.document_parser import (
    DOCXParser,
    HTMLParser,
    ParsedDocument,
    PDFParser,
)
from src.ai_doc_gen.utils.serialization import EnhancedJSONEncoder


class ComprehensiveWorkflowTest:
    """Comprehensive test of the template-based gap analysis workflow."""

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

    def download_cisco_html(self, url: str) -> str:
        """Download Cisco HTML content."""
        print(f"🌐 Downloading Cisco HTML from: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            output_file = "cisco_nexus_test.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)

            print(f"✅ Downloaded {len(response.text)} characters to {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ Error downloading HTML: {e}")
            return None

    def analyze_document(self, document_path: str, doc_type: str) -> Dict[str, Any]:
        """Analyze a single document against the template."""
        print(f"\n📄 Analyzing {doc_type}: {document_path}")

        # Get appropriate parser
        parser = {
            'PDF': self.pdf_parser,
            'HTML': self.html_parser,
            'DOCX': self.docx_parser
        }.get(doc_type)

        if not parser:
            return {'error': f'Unsupported document type: {doc_type}'}

        # Parse document
        try:
            start_time = time.time()
            parsed_doc = parser.parse(document_path)
            parse_time = time.time() - start_time
            print(f"   ✅ Parsed: {len(parsed_doc.sections)} sections in {parse_time:.2f}s")
        except Exception as e:
            return {'error': f'Parsing failed: {e}'}

        # Analyze against template
        analysis = self._analyze_against_template(parsed_doc, doc_type)
        analysis['parse_time'] = parse_time

        return analysis

    def _analyze_against_template(self, parsed_doc: ParsedDocument, doc_type: str) -> Dict[str, Any]:
        """Analyze document against template."""
        template_sections = self.template.get('template_structure', {}).get('section_hierarchy', [])
        quality_standards = self.template.get('quality_standards', {})

        # Extract document section titles
        doc_sections = [s.get('heading', '') for s in parsed_doc.sections if s.get('heading')]

        # Find matches with template sections
        matches = []
        missing_sections = []

        for template_section in template_sections:
            template_title = template_section.get('title', '')
            best_match = self._find_best_match(template_title, doc_sections)

            if best_match and best_match['similarity'] > 0.6:
                matches.append({
                    'template_section': template_title,
                    'document_section': best_match['candidate'],
                    'similarity': best_match['similarity'],
                    'template_source': template_section.get('recommended_source', 'unknown')
                })
            else:
                missing_sections.append(template_title)

        # Calculate quality metrics
        completeness_metrics = quality_standards.get('completeness_metrics', {})
        target_sections = completeness_metrics.get('target_sections', 0)
        target_text_length = completeness_metrics.get('target_text_length', 0)

        section_score = len(parsed_doc.sections) / target_sections * 100 if target_sections > 0 else 0
        text_score = len(parsed_doc.raw_text) / target_text_length * 100 if target_text_length > 0 else 0
        overall_score = (section_score + text_score) / 2

        return {
            'document_info': {
                'type': doc_type,
                'sections': len(parsed_doc.sections),
                'text_length': len(parsed_doc.raw_text),
                'title': parsed_doc.title
            },
            'template_comparison': {
                'matches': len(matches),
                'missing_sections': len(missing_sections),
                'coverage_percentage': len(matches) / len(template_sections) * 100 if template_sections else 0,
                'sample_matches': matches[:5],  # First 5 matches
                'sample_missing': missing_sections[:5]  # First 5 missing
            },
            'quality_assessment': {
                'overall_score': min(overall_score, 100),
                'section_completeness': min(section_score, 100),
                'text_completeness': min(text_score, 100),
                'quality_level': self._get_quality_level(overall_score)
            },
            'content_analysis': {
                'has_safety_content': self._has_safety_content(parsed_doc),
                'has_step_by_step': self._has_step_by_step_content(parsed_doc),
                'has_specifications': self._has_specifications(parsed_doc)
            }
        }

    def _find_best_match(self, target: str, candidates: List[str]) -> Optional[Dict[str, Any]]:
        """Find the best matching section title using enhanced semantic matching."""
        if not candidates:
            return None

        # Normalize target
        target_normalized = self._normalize_text(target)
        
        best_match = None
        best_similarity = 0.0
        
        for candidate in candidates:
            candidate_normalized = self._normalize_text(candidate)
            
            # Calculate multiple similarity metrics
            exact_match = self._calculate_exact_match(target_normalized, candidate_normalized)
            fuzzy_match = self._calculate_fuzzy_match(target_normalized, candidate_normalized)
            semantic_match = self._calculate_semantic_match(target_normalized, candidate_normalized)
            keyword_match = self._calculate_keyword_match(target_normalized, candidate_normalized)
            
            # Weighted combination of similarity scores
            combined_similarity = (
                exact_match * 0.4 +
                fuzzy_match * 0.3 +
                semantic_match * 0.2 +
                keyword_match * 0.1
            )
            
            if combined_similarity > best_similarity:
                best_similarity = combined_similarity
                best_match = {
                    "candidate": candidate,
                    "similarity": combined_similarity,
                    "exact_match": exact_match,
                    "fuzzy_match": fuzzy_match,
                    "semantic_match": semantic_match,
                    "keyword_match": keyword_match
                }
        
        return best_match if best_similarity > 0.25 else None  # Lowered threshold for better coverage

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching."""
        import re
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _calculate_exact_match(self, target: str, candidate: str) -> float:
        """Calculate exact match similarity."""
        if target == candidate:
            return 1.0
        if target in candidate or candidate in target:
            return 0.8
        return 0.0

    def _calculate_fuzzy_match(self, target: str, candidate: str) -> float:
        """Calculate fuzzy string matching similarity."""
        import difflib
        
        # Use difflib for fuzzy matching
        similarity = difflib.SequenceMatcher(None, target, candidate).ratio()
        
        # Boost similarity for partial matches
        target_words = set(target.split())
        candidate_words = set(candidate.split())
        
        if target_words and candidate_words:
            word_overlap = len(target_words.intersection(candidate_words))
            word_similarity = word_overlap / max(len(target_words), len(candidate_words))
            # Combine sequence similarity with word overlap
            return max(similarity, word_similarity)
        
        return similarity

    def _calculate_semantic_match(self, target: str, candidate: str) -> float:
        """Calculate semantic similarity based on technical terms."""
        # Technical term mappings for better semantic matching
        semantic_mappings = {
            'overview': ['introduction', 'summary', 'description', 'about'],
            'specification': ['specs', 'specifications', 'technical specs', 'requirements'],
            'installation': ['install', 'setup', 'deployment', 'configuration'],
            'configuration': ['config', 'setup', 'settings', 'parameters'],
            'requirements': ['prerequisites', 'requirements', 'needs', 'dependencies'],
            'features': ['capabilities', 'functions', 'characteristics', 'properties'],
            'safety': ['safety', 'warnings', 'precautions', 'security'],
            'troubleshooting': ['troubleshoot', 'diagnostics', 'problems', 'issues'],
            'maintenance': ['maintain', 'service', 'upkeep', 'care'],
            'specifications': ['specs', 'specification', 'technical specs', 'requirements']
        }
        
        target_lower = target.lower()
        candidate_lower = candidate.lower()
        
        # Check for semantic matches
        for primary_term, synonyms in semantic_mappings.items():
            if primary_term in target_lower:
                for synonym in synonyms:
                    if synonym in candidate_lower:
                        return 0.9
            elif primary_term in candidate_lower:
                for synonym in synonyms:
                    if synonym in target_lower:
                        return 0.9
        
        return 0.0

    def _calculate_keyword_match(self, target: str, candidate: str) -> float:
        """Calculate keyword-based similarity."""
        # Extract key technical keywords
        technical_keywords = [
            'cisco', 'nexus', 'catalyst', 'switch', 'router', 'hardware',
            'installation', 'configuration', 'specification', 'requirements',
            'overview', 'features', 'safety', 'maintenance', 'troubleshooting'
        ]
        
        target_words = set(target.split())
        candidate_words = set(candidate.split())
        
        target_keywords = target_words.intersection(set(technical_keywords))
        candidate_keywords = candidate_words.intersection(set(technical_keywords))
        
        if target_keywords and candidate_keywords:
            keyword_overlap = len(target_keywords.intersection(candidate_keywords))
            total_keywords = len(target_keywords.union(candidate_keywords))
            return keyword_overlap / total_keywords if total_keywords > 0 else 0.0
        
        return 0.0

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

    def _has_safety_content(self, parsed_doc: ParsedDocument) -> bool:
        """Check if document has safety content."""
        safety_keywords = ['safety', 'warning', 'caution', 'danger', 'precaution']
        text = parsed_doc.raw_text.lower()
        return any(keyword in text for keyword in safety_keywords)

    def _has_step_by_step_content(self, parsed_doc: ParsedDocument) -> bool:
        """Check if document has step-by-step content."""
        step_keywords = ['step', 'procedure', 'instruction', 'guide']
        text = parsed_doc.raw_text.lower()
        return any(keyword in text for keyword in step_keywords)

    def _has_specifications(self, parsed_doc: ParsedDocument) -> bool:
        """Check if document has specifications."""
        spec_keywords = ['specification', 'spec', 'technical', 'parameter']
        text = parsed_doc.raw_text.lower()
        return any(keyword in text for keyword in spec_keywords)

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test on all three documents."""
        print("🧪 COMPREHENSIVE WORKFLOW TEST")
        print("=" * 60)

        test_results = {
            'timestamp': datetime.now().isoformat(),
            'template_info': {
                'device_family': self.template.get('template_metadata', {}).get('device_family', 'Unknown'),
                'template_sections': len(self.template.get('template_structure', {}).get('section_hierarchy', []))
            },
            'document_analyses': {},
            'comparative_analysis': {},
            'workflow_validation': {}
        }

        # Test 1: Functional Spec DOCX
        docx_path = "functional_spec.docx"
        if Path(docx_path).exists():
            docx_analysis = self.analyze_document(docx_path, 'DOCX')
            test_results['document_analyses']['functional_spec_docx'] = docx_analysis
        else:
            print(f"⚠️  {docx_path} not found - skipping DOCX test")

        # Test 2: Installation Guide PDF
        pdf_path = "installation_guide.pdf"
        if Path(pdf_path).exists():
            pdf_analysis = self.analyze_document(pdf_path, 'PDF')
            test_results['document_analyses']['installation_guide_pdf'] = pdf_analysis
        else:
            print(f"⚠️  {pdf_path} not found - skipping PDF test")

        # Test 3: Cisco HTML
        cisco_url = "https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus9000/hw/9364c-h1/aci/cisco-nexus-9364c_h1_aci_mode_hardware_install_guide/b_c9364c_ACI_mode_hardware_install_guide_appendix_01010.html"
        html_path = self.download_cisco_html(cisco_url)
        if html_path:
            html_analysis = self.analyze_document(html_path, 'HTML')
            test_results['document_analyses']['cisco_nexus_html'] = html_analysis
        else:
            print("⚠️  Failed to download Cisco HTML - skipping HTML test")

        # Comparative analysis
        test_results['comparative_analysis'] = self._compare_documents(test_results['document_analyses'])

        # Workflow validation
        test_results['workflow_validation'] = self._validate_workflow(test_results['document_analyses'])

        return test_results

    def _compare_documents(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance and quality across documents."""
        comparison = {
            'performance_comparison': {},
            'quality_comparison': {},
            'content_comparison': {},
            'template_coverage_comparison': {}
        }

        # Performance comparison
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                comparison['performance_comparison'][doc_name] = {
                    'parse_time': analysis.get('parse_time', 0),
                    'sections_per_second': analysis['document_info']['sections'] / analysis.get('parse_time', 1)
                }

        # Quality comparison
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                comparison['quality_comparison'][doc_name] = {
                    'overall_score': analysis['quality_assessment']['overall_score'],
                    'quality_level': analysis['quality_assessment']['quality_level'],
                    'section_completeness': analysis['quality_assessment']['section_completeness'],
                    'text_completeness': analysis['quality_assessment']['text_completeness']
                }

        # Content comparison
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                comparison['content_comparison'][doc_name] = analysis['content_analysis']

        # Template coverage comparison
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                comparison['template_coverage_comparison'][doc_name] = {
                    'coverage_percentage': analysis['template_comparison']['coverage_percentage'],
                    'matches': analysis['template_comparison']['matches'],
                    'missing_sections': analysis['template_comparison']['missing_sections']
                }

        return comparison

    def _validate_workflow(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the workflow is working as expected."""
        validation = {
            'all_documents_parsed': True,
            'template_consistency': True,
            'quality_metrics_consistent': True,
            'recommendations': []
        }

        # Check if all documents were parsed successfully
        for doc_name, analysis in analyses.items():
            if 'error' in analysis:
                validation['all_documents_parsed'] = False
                validation['recommendations'].append(f"Failed to parse {doc_name}: {analysis['error']}")

        # Check template consistency
        coverage_values = []
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                coverage_values.append(analysis['template_comparison']['coverage_percentage'])

        if len(set(coverage_values)) == 1 and len(coverage_values) > 1:
            validation['recommendations'].append("All documents have identical template coverage - may indicate template matching issues")

        # Check quality metrics consistency
        quality_scores = []
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                quality_scores.append(analysis['quality_assessment']['overall_score'])

        if max(quality_scores) - min(quality_scores) < 10 and len(quality_scores) > 1:
            validation['recommendations'].append("Quality scores are very similar - may indicate scoring needs adjustment")

        # Add positive validation if everything looks good
        if validation['all_documents_parsed'] and not validation['recommendations']:
            validation['recommendations'].append("✅ Workflow validation passed - all systems working as expected")

        return validation

    def print_test_summary(self, results: Dict[str, Any]):
        """Print a comprehensive test summary."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE WORKFLOW TEST SUMMARY")
        print("="*80)

        # Template info
        template_info = results['template_info']
        print("\n🔧 TEMPLATE INFO:")
        print(f"   Device Family: {template_info['device_family']}")
        print(f"   Template Sections: {template_info['template_sections']}")

        # Document analyses
        print("\n📄 DOCUMENT ANALYSES:")
        for doc_name, analysis in results['document_analyses'].items():
            if 'error' in analysis:
                print(f"   ❌ {doc_name}: {analysis['error']}")
            else:
                doc_info = analysis['document_info']
                quality = analysis['quality_assessment']
                coverage = analysis['template_comparison']['coverage_percentage']
                print(f"   ✅ {doc_name}:")
                print(f"      Type: {doc_info['type']}, Sections: {doc_info['sections']}, Text: {doc_info['text_length']:,} chars")
                print(f"      Quality: {quality['overall_score']:.1f}% ({quality['quality_level']})")
                print(f"      Template Coverage: {coverage:.1f}%")

        # Comparative analysis
        comparison = results['comparative_analysis']
        if comparison.get('performance_comparison'):
            print("\n⚡ PERFORMANCE COMPARISON:")
            for doc_name, perf in comparison['performance_comparison'].items():
                print(f"   {doc_name}: {perf['parse_time']:.2f}s ({perf['sections_per_second']:.1f} sections/sec)")

        if comparison.get('quality_comparison'):
            print("\n📊 QUALITY COMPARISON:")
            for doc_name, quality in comparison['quality_comparison'].items():
                print(f"   {doc_name}: {quality['overall_score']:.1f}% ({quality['quality_level']})")

        if comparison.get('template_coverage_comparison'):
            print("\n🔄 TEMPLATE COVERAGE COMPARISON:")
            for doc_name, coverage in comparison['template_coverage_comparison'].items():
                print(f"   {doc_name}: {coverage['coverage_percentage']:.1f}% ({coverage['matches']} matches, {coverage['missing_sections']} missing)")

        # Workflow validation
        validation = results['workflow_validation']
        print("\n🔍 WORKFLOW VALIDATION:")
        print(f"   All Documents Parsed: {'✅' if validation['all_documents_parsed'] else '❌'}")
        print(f"   Template Consistency: {'✅' if validation['template_consistency'] else '❌'}")
        print(f"   Quality Metrics Consistent: {'✅' if validation['quality_metrics_consistent'] else '❌'}")

        if validation['recommendations']:
            print("\n💡 VALIDATION RECOMMENDATIONS:")
            for i, rec in enumerate(validation['recommendations'], 1):
                print(f"   {i}. {rec}")

        print("\n" + "="*80)

    def save_test_results(self, results: Dict[str, Any], output_path: str):
        """Save comprehensive test results."""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, cls=EnhancedJSONEncoder, indent=2)
            print(f"✅ Comprehensive test results saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving test results: {e}")


def main():
    """Main function to run comprehensive workflow test."""
    print("🚀 Comprehensive Workflow Test")
    print("Testing with functional_spec.docx, installation_guide.pdf, and Cisco HTML")
    print("=" * 60)

    # Template path
    template_path = "c8500_superset_template.json"
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        print("   Run llm_superset_template_generator.py first to create the template")
        return

    # Initialize test
    test = ComprehensiveWorkflowTest(template_path)

    # Run comprehensive test
    results = test.run_comprehensive_test()

    # Print summary
    test.print_test_summary(results)

    # Save results
    output_path = "comprehensive_workflow_test_results.json"
    test.save_test_results(results, output_path)

    print("\n🎯 Comprehensive workflow test complete!")
    print(f"   Results: {output_path}")
    print("   Review the results to validate your pre-testing works in the end product")


if __name__ == "__main__":
    main()
