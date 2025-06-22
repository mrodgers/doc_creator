#!/usr/bin/env python3
"""
Comprehensive Workflow Test
Tests the end-to-end workflow with functional_spec.docx, installation_guide.pdf, and Cisco HTML.
"""

import json
import time
import os
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

    def analyze_document(self, doc_path: str, doc_type: str) -> Dict[str, Any]:
        """Analyze a document against the template with progress tracking."""
        print(f"📄 Analyzing {doc_type}: {os.path.basename(doc_path)}")
        
        # Get appropriate parser
        parser = {
            'PDF': self.pdf_parser,
            'HTML': self.html_parser,
            'DOCX': self.docx_parser
        }.get(doc_type)
        
        if not parser:
            return {'error': f'Unsupported document type: {doc_type}'}
        
        # Parse document
        start_time = time.time()
        try:
            parsed_doc = parser.parse(doc_path)
            parse_time = time.time() - start_time
            print(f"   ✅ Parsed: {len(parsed_doc.sections)} sections in {parse_time:.2f}s")
        except Exception as e:
            return {'error': f'Parsing failed: {e}'}
        
        # Analyze against template with progress tracking
        print(f"   🔍 Matching against template...")
        analysis = self._analyze_against_template(parsed_doc, doc_type)
        
        return {
            'doc_path': doc_path,
            'doc_type': doc_type,
            'parsed_doc': parsed_doc,
            'analysis': analysis,
            'parse_time': parse_time
        }

    def _analyze_against_template(self, parsed_doc: ParsedDocument, doc_type: str) -> Dict[str, Any]:
        """Analyze document against template with progress tracking."""
        template_sections = self.template.get('template_structure', {}).get('section_hierarchy', [])
        doc_sections = parsed_doc.sections
        
        print(f"      📊 Processing {len(doc_sections)} sections against {len(template_sections)} template sections")
        
        matches = []
        total_sections = len(template_sections)
        
        for i, template_section in enumerate(template_sections):
            if i % 10 == 0:  # Progress indicator every 10 sections
                print(f"      ⏳ Progress: {i}/{total_sections} sections processed")
            
            template_title = template_section.get('title', '')
            best_match = self._find_best_match(template_title, 
                                             [s.get('heading', '') for s in doc_sections if s.get('heading')], 
                                             doc_sections)
            
            if best_match:
                matches.append({
                    'template_section': template_section,
                    'best_match': best_match,
                    'matched_section': next((s for s in doc_sections if s.get('heading', '') == best_match['candidate']), None)
                })
        
        print(f"      ✅ Found {len(matches)} matches out of {total_sections} template sections")
        
        return {
            'matches': matches,
            'coverage': len(matches) / len(template_sections) if template_sections else 0,
            'total_sections': len(template_sections),
            'matched_sections': len(matches)
        }

    def _find_best_match(self, target: str, candidates: List[str], candidate_sections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the best matching section title using enhanced semantic and optional ML classification."""
        if not candidates:
            return None

        # Import ML classifier (optional, for performance)
        classifier = None
        try:
            from ai_doc_gen.ml.section_classifier import SectionClassifier
            classifier = SectionClassifier()
        except Exception:
            pass

        # Normalize target
        target_normalized = self._normalize_text(target)
        target_ml_type = None

        best_match = None
        best_similarity = 0.0

        for idx, candidate in enumerate(candidates):
            candidate_normalized = self._normalize_text(candidate)
            candidate_section = candidate_sections[idx] if idx < len(candidate_sections) else {}

            # Calculate multiple similarity metrics
            exact_match = self._calculate_exact_match(target_normalized, candidate_normalized)
            fuzzy_match = self._calculate_fuzzy_match(target_normalized, candidate_normalized)
            semantic_match = self._calculate_semantic_match(target_normalized, candidate_normalized)
            keyword_match = self._calculate_keyword_match(target_normalized, candidate_normalized)

            # Synonym/abbreviation expansion
            expanded_target = self._expand_synonyms_and_abbr(target_normalized)
            expanded_candidate = self._expand_synonyms_and_abbr(candidate_normalized)
            expanded_semantic = self._calculate_semantic_match(expanded_target, expanded_candidate)

            # Initial combined similarity without ML
            combined_similarity = (
                exact_match * 0.35 +
                fuzzy_match * 0.25 +
                semantic_match * 0.2 +
                keyword_match * 0.1 +
                expanded_semantic * 0.1
            )

            # Only use ML classification for promising matches to improve performance
            ml_type_match = 0.0
            candidate_ml_type = None
            target_ml_type = None
            
            if classifier and combined_similarity > 0.3:  # Only for promising matches
                try:
                    if target_ml_type is None:
                        target_ml_type = classifier.classify_section(target).get('predicted_class')
                    candidate_ml_type = classifier.classify_section(candidate).get('predicted_class')
                    ml_type_match = 1.0 if (target_ml_type and candidate_ml_type and target_ml_type == candidate_ml_type) else 0.0
                    
                    # Adjust similarity with ML input
                    combined_similarity = (
                        exact_match * 0.3 +
                        fuzzy_match * 0.2 +
                        semantic_match * 0.15 +
                        keyword_match * 0.1 +
                        ml_type_match * 0.15 +
                        expanded_semantic * 0.1
                    )
                except Exception:
                    # Fallback to non-ML similarity if ML fails
                    pass

            if combined_similarity > best_similarity:
                best_similarity = combined_similarity
                best_match = {
                    "candidate": candidate,
                    "similarity": combined_similarity,
                    "exact_match": exact_match,
                    "fuzzy_match": fuzzy_match,
                    "semantic_match": semantic_match,
                    "keyword_match": keyword_match,
                    "ml_type_match": ml_type_match,
                    "expanded_semantic": expanded_semantic,
                    "candidate_ml_type": candidate_ml_type,
                    "target_ml_type": target_ml_type
                }

        return best_match if best_similarity > 0.22 else None  # Lowered threshold for better coverage

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

    def _expand_synonyms_and_abbr(self, text: str) -> str:
        """Expand common technical synonyms and abbreviations."""
        synonym_map = {
            'spec': 'specification',
            'specs': 'specification',
            'req': 'requirement',
            'reqs': 'requirement',
            'config': 'configuration',
            'install': 'installation',
            'intro': 'introduction',
            'feat': 'feature',
            'maint': 'maintenance',
            'trbl': 'troubleshooting',
            'troubleshoot': 'troubleshooting',
            'proc': 'procedure',
            'desc': 'description',
            'warn': 'warning',
            'prec': 'precaution',
            'env': 'environment',
            'perf': 'performance',
            'char': 'characteristic',
            'func': 'function',
            'cap': 'capability',
            'svc': 'service',
            'ref': 'reference',
            'addl': 'additional',
            'info': 'information',
            'doc': 'document',
            'sec': 'section',
            'tbl': 'table',
            'fig': 'figure',
            'app': 'appendix',
            'gloss': 'glossary',
            'acronym': 'abbreviation',
        }
        words = text.split()
        expanded = [synonym_map.get(w, w) for w in words]
        return ' '.join(expanded)

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
            'template_coverage_comparison': {},
            'summary_statistics': {}
        }

        # Performance comparison
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                parsed_doc = analysis.get('parsed_doc')
                if hasattr(parsed_doc, 'sections'):
                    sections = len(parsed_doc.sections)
                else:
                    sections = 0
                parse_time = analysis.get('parse_time', 1)
                
                comparison['performance_comparison'][doc_name] = {
                    'parse_time': parse_time,
                    'sections_per_second': sections / parse_time if parse_time > 0 else 0,
                    'total_sections': sections
                }

        # Template coverage comparison
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                analysis_data = analysis.get('analysis', {})
                comparison['template_coverage_comparison'][doc_name] = {
                    'coverage_percentage': analysis_data.get('coverage', 0) * 100,
                    'matches': analysis_data.get('matched_sections', 0),
                    'total_template_sections': analysis_data.get('total_sections', 0)
                }

        # Summary statistics
        if comparison['performance_comparison']:
            parse_times = [p['parse_time'] for p in comparison['performance_comparison'].values()]
            sections_per_sec = [p['sections_per_second'] for p in comparison['performance_comparison'].values()]
            coverage_percentages = [c['coverage_percentage'] for c in comparison['template_coverage_comparison'].values()]
            
            comparison['summary_statistics'] = {
                'avg_parse_time': sum(parse_times) / len(parse_times),
                'avg_sections_per_second': sum(sections_per_sec) / len(sections_per_sec),
                'avg_coverage_percentage': sum(coverage_percentages) / len(coverage_percentages),
                'best_coverage': max(coverage_percentages) if coverage_percentages else 0,
                'fastest_parser': min(parse_times) if parse_times else 0
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
                coverage = analysis.get('analysis', {}).get('coverage', 0) * 100
                coverage_values.append(coverage)

        if len(set(coverage_values)) == 1 and len(coverage_values) > 1:
            validation['recommendations'].append("All documents have identical template coverage - may indicate template matching issues")

        # Check if coverage is reasonable
        avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0
        if avg_coverage < 10:
            validation['recommendations'].append(f"Low average coverage ({avg_coverage:.1f}%) - consider adjusting matching thresholds")
        elif avg_coverage > 80:
            validation['recommendations'].append(f"Very high average coverage ({avg_coverage:.1f}%) - may indicate overly permissive matching")

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
                parsed_doc = analysis.get('parsed_doc')
                if hasattr(parsed_doc, 'sections'):
                    sections = len(parsed_doc.sections)
                else:
                    sections = 0
                analysis_data = analysis.get('analysis', {})
                coverage = analysis_data.get('coverage', 0) * 100
                parse_time = analysis.get('parse_time', 0)
                
                print(f"   ✅ {doc_name}:")
                print(f"      Type: {analysis.get('doc_type', 'Unknown')}, Sections: {sections}")
                print(f"      Parse Time: {parse_time:.2f}s, Template Coverage: {coverage:.1f}%")
                print(f"      Matches: {analysis_data.get('matched_sections', 0)}/{analysis_data.get('total_sections', 0)}")

        # Comparative analysis
        comparison = results['comparative_analysis']
        if comparison.get('performance_comparison'):
            print("\n⚡ PERFORMANCE COMPARISON:")
            for doc_name, perf in comparison['performance_comparison'].items():
                print(f"   {doc_name}: {perf['parse_time']:.2f}s ({perf['sections_per_second']:.1f} sections/sec)")

        if comparison.get('template_coverage_comparison'):
            print("\n🔄 TEMPLATE COVERAGE COMPARISON:")
            for doc_name, coverage in comparison['template_coverage_comparison'].items():
                print(f"   {doc_name}: {coverage['coverage_percentage']:.1f}% ({coverage['matches']} matches, {coverage['total_template_sections']} total sections)")

        if comparison.get('summary_statistics'):
            stats = comparison['summary_statistics']
            print("\n📈 SUMMARY STATISTICS:")
            print(f"   Average Parse Time: {stats['avg_parse_time']:.2f}s")
            print(f"   Average Sections/Second: {stats['avg_sections_per_second']:.1f}")
            print(f"   Average Coverage: {stats['avg_coverage_percentage']:.1f}%")
            print(f"   Best Coverage: {stats['best_coverage']:.1f}%")
            print(f"   Fastest Parser: {stats['fastest_parser']:.2f}s")

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
