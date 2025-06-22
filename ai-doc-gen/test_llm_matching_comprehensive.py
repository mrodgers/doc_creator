#!/usr/bin/env python3
"""
Comprehensive LLM Matching Test
Tests LLM-enhanced matching on all three documents to evaluate prompt effectiveness.
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from llm_enhanced_matcher import LLMEnhancedMatcher


class ComprehensiveLLMMatchingTest:
    """Comprehensive test of LLM-enhanced section matching."""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.matcher = LLMEnhancedMatcher(template_path)
        
    def download_cisco_html(self, url: str) -> str:
        """Download Cisco HTML content."""
        print(f"🌐 Downloading Cisco HTML from: {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            output_file = "cisco_nexus_llm_test.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✅ Downloaded {len(response.text)} characters to {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error downloading HTML: {e}")
            return None
    
    def test_all_documents(self) -> Dict[str, Any]:
        """Test LLM matching on all three documents."""
        print("🧪 COMPREHENSIVE LLM MATCHING TEST")
        print("=" * 60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'document_analyses': {},
            'prompt_evaluation': {},
            'recommendations': []
        }
        
        # Test 1: Functional Spec DOCX
        docx_path = "functional_spec.docx"
        if Path(docx_path).exists():
            print(f"\n📄 Testing DOCX: {docx_path}")
            docx_analysis = self.matcher.analyze_document_with_llm_matching(docx_path)
            test_results['document_analyses']['functional_spec_docx'] = docx_analysis
        else:
            print(f"⚠️  {docx_path} not found - skipping DOCX test")
        
        # Test 2: Installation Guide PDF
        pdf_path = "installation_guide.pdf"
        if Path(pdf_path).exists():
            print(f"\n📄 Testing PDF: {pdf_path}")
            pdf_analysis = self.matcher.analyze_document_with_llm_matching(pdf_path)
            test_results['document_analyses']['installation_guide_pdf'] = pdf_analysis
        else:
            print(f"⚠️  {pdf_path} not found - skipping PDF test")
        
        # Test 3: Cisco HTML
        cisco_url = "https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus9000/hw/9364c-h1/aci/cisco-nexus-9364c_h1_aci_mode_hardware_install_guide/b_c9364c_ACI_mode_hardware_install_guide_appendix_01010.html"
        html_path = self.download_cisco_html(cisco_url)
        if html_path:
            print(f"\n📄 Testing HTML: {html_path}")
            html_analysis = self.matcher.analyze_document_with_llm_matching(html_path)
            test_results['document_analyses']['cisco_nexus_html'] = html_analysis
        else:
            print("⚠️  Failed to download Cisco HTML - skipping HTML test")
        
        # Evaluate prompt effectiveness
        test_results['prompt_evaluation'] = self._evaluate_prompt_effectiveness(test_results['document_analyses'])
        
        # Generate recommendations
        test_results['recommendations'] = self._generate_prompt_recommendations(test_results)
        
        return test_results
    
    def _evaluate_prompt_effectiveness(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the effectiveness of the LLM prompts."""
        evaluation = {
            'overall_performance': {},
            'matching_quality': {},
            'prompt_issues': [],
            'success_metrics': {}
        }
        
        total_improvements = []
        total_matches = 0
        total_traditional_matches = 0
        confidence_scores = []
        reasoning_quality = []
        
        for doc_name, analysis in analyses.items():
            if 'error' in analysis:
                continue
                
            comparison = analysis.get('comparison', {})
            llm_matches = analysis.get('llm_matching', {}).get('matches', [])
            
            # Collect metrics
            improvement = comparison.get('improvement', 0)
            total_improvements.append(improvement)
            
            llm_match_count = comparison.get('llm_matches_count', 0)
            traditional_match_count = comparison.get('traditional_matches_count', 0)
            total_matches += llm_match_count
            total_traditional_matches += traditional_match_count
            
            # Analyze match quality
            for match in llm_matches:
                confidence = match.get('confidence', 0)
                reasoning = match.get('reasoning', '')
                
                confidence_scores.append(confidence)
                
                # Evaluate reasoning quality
                reasoning_score = self._evaluate_reasoning_quality(reasoning)
                reasoning_quality.append(reasoning_score)
        
        # Calculate overall metrics
        if total_improvements:
            avg_improvement = sum(total_improvements) / len(total_improvements)
            max_improvement = max(total_improvements)
            min_improvement = min(total_improvements)
        else:
            avg_improvement = max_improvement = min_improvement = 0
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            high_confidence_matches = len([c for c in confidence_scores if c >= 0.8])
            low_confidence_matches = len([c for c in confidence_scores if c < 0.7])
        else:
            avg_confidence = high_confidence_matches = low_confidence_matches = 0
        
        if reasoning_quality:
            avg_reasoning_quality = sum(reasoning_quality) / len(reasoning_quality)
        else:
            avg_reasoning_quality = 0
        
        # Identify potential prompt issues
        prompt_issues = []
        
        if avg_improvement < 5:
            prompt_issues.append("Low average improvement - prompts may not be specific enough")
        
        if avg_confidence < 0.7:
            prompt_issues.append("Low average confidence - prompts may need refinement")
        
        if low_confidence_matches > high_confidence_matches:
            prompt_issues.append("More low-confidence than high-confidence matches - prompts may be too broad")
        
        if avg_reasoning_quality < 0.6:
            prompt_issues.append("Poor reasoning quality - prompts may not encourage detailed explanations")
        
        # Check for specific matching patterns
        for doc_name, analysis in analyses.items():
            if 'error' not in analysis:
                llm_matches = analysis.get('llm_matching', {}).get('matches', [])
                if len(llm_matches) == 0:
                    prompt_issues.append(f"No LLM matches found for {doc_name} - prompts may be too restrictive")
        
        evaluation['overall_performance'] = {
            'average_improvement': avg_improvement,
            'max_improvement': max_improvement,
            'min_improvement': min_improvement,
            'total_llm_matches': total_matches,
            'total_traditional_matches': total_traditional_matches,
            'improvement_ratio': total_matches / total_traditional_matches if total_traditional_matches > 0 else 0
        }
        
        evaluation['matching_quality'] = {
            'average_confidence': avg_confidence,
            'high_confidence_matches': high_confidence_matches,
            'low_confidence_matches': low_confidence_matches,
            'average_reasoning_quality': avg_reasoning_quality,
            'total_matches_analyzed': len(confidence_scores)
        }
        
        evaluation['prompt_issues'] = prompt_issues
        
        # Calculate effectiveness score first
        effectiveness_score = self._calculate_prompt_effectiveness_score(evaluation)
        
        evaluation['success_metrics'] = {
            'prompt_effectiveness_score': effectiveness_score,
            'recommendations_needed': len(prompt_issues) > 0,
            'overall_assessment': self._assess_overall_prompt_performance(effectiveness_score)
        }
        
        return evaluation
    
    def _evaluate_reasoning_quality(self, reasoning: str) -> float:
        """Evaluate the quality of LLM reasoning."""
        if not reasoning:
            return 0.0
        
        score = 0.0
        
        # Check for specific technical terms
        technical_terms = ['installation', 'safety', 'requirements', 'specifications', 'procedures', 'configuration']
        tech_term_count = sum(1 for term in technical_terms if term.lower() in reasoning.lower())
        score += min(tech_term_count / 3, 0.3)  # Max 0.3 for technical terms
        
        # Check for logical connectors
        logical_connectors = ['because', 'since', 'therefore', 'thus', 'as', 'while', 'although']
        connector_count = sum(1 for connector in logical_connectors if connector.lower() in reasoning.lower())
        score += min(connector_count / 2, 0.2)  # Max 0.2 for logical connectors
        
        # Check for content-specific reasoning
        if len(reasoning) > 20:
            score += 0.2  # Reasonable length
        
        if 'content' in reasoning.lower() or 'purpose' in reasoning.lower() or 'intent' in reasoning.lower():
            score += 0.3  # Shows understanding of content analysis
        
        return min(score, 1.0)
    
    def _calculate_prompt_effectiveness_score(self, evaluation: Dict[str, Any]) -> float:
        """Calculate overall prompt effectiveness score."""
        score = 0.0
        
        # Improvement factor (40% weight)
        avg_improvement = evaluation['overall_performance']['average_improvement']
        score += min(avg_improvement / 10, 1.0) * 0.4  # Normalize to 10% improvement
        
        # Confidence factor (30% weight)
        avg_confidence = evaluation['matching_quality']['average_confidence']
        score += avg_confidence * 0.3
        
        # Reasoning quality factor (20% weight)
        avg_reasoning = evaluation['matching_quality']['average_reasoning_quality']
        score += avg_reasoning * 0.2
        
        # Issue factor (10% weight)
        issue_count = len(evaluation['prompt_issues'])
        score += max(0, 1.0 - issue_count * 0.1) * 0.1  # Deduct for each issue
        
        return min(score, 1.0)
    
    def _assess_overall_prompt_performance(self, effectiveness_score: float) -> str:
        """Assess overall prompt performance."""
        if effectiveness_score >= 0.8:
            return "Excellent"
        elif effectiveness_score >= 0.6:
            return "Good"
        elif effectiveness_score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_prompt_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for prompt improvement."""
        recommendations = []
        evaluation = test_results['prompt_evaluation']
        
        # Performance-based recommendations
        avg_improvement = evaluation['overall_performance']['average_improvement']
        if avg_improvement < 5:
            recommendations.append("Increase prompt specificity - add more technical domain examples")
        
        avg_confidence = evaluation['matching_quality']['average_confidence']
        if avg_confidence < 0.7:
            recommendations.append("Add confidence thresholds and examples to improve match quality")
        
        # Issue-based recommendations
        for issue in evaluation['prompt_issues']:
            if "too restrictive" in issue.lower():
                recommendations.append("Lower confidence threshold or add more flexible matching criteria")
            elif "too broad" in issue.lower():
                recommendations.append("Add more specific matching criteria and examples")
            elif "reasoning quality" in issue.lower():
                recommendations.append("Enhance prompt to encourage detailed technical reasoning")
        
        # Success-based recommendations
        effectiveness_score = evaluation['success_metrics']['prompt_effectiveness_score']
        if effectiveness_score >= 0.8:
            recommendations.append("Prompts are working well - consider fine-tuning for edge cases")
        elif effectiveness_score >= 0.6:
            recommendations.append("Prompts show promise - focus on improving confidence and reasoning")
        else:
            recommendations.append("Significant prompt improvements needed - consider complete redesign")
        
        return recommendations
    
    def print_comprehensive_results(self, results: Dict[str, Any]):
        """Print comprehensive test results."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE LLM MATCHING TEST RESULTS")
        print("="*80)
        
        # Document analyses summary
        print(f"\n📄 DOCUMENT ANALYSES SUMMARY:")
        for doc_name, analysis in results['document_analyses'].items():
            if 'error' in analysis:
                print(f"   ❌ {doc_name}: {analysis['error']}")
            else:
                comparison = analysis.get('comparison', {})
                llm_coverage = comparison.get('llm_coverage', 0)
                improvement = comparison.get('improvement', 0)
                print(f"   ✅ {doc_name}:")
                print(f"      LLM Coverage: {llm_coverage:.1f}%")
                print(f"      Improvement: {improvement:.1f}%")
                print(f"      Matches: {comparison.get('llm_matches_count', 0)}")
        
        # Prompt evaluation
        evaluation = results['prompt_evaluation']
        print(f"\n🤖 PROMPT EFFECTIVENESS EVALUATION:")
        
        overall_perf = evaluation['overall_performance']
        print(f"   Average Improvement: {overall_perf['average_improvement']:.1f}%")
        print(f"   Max Improvement: {overall_perf['max_improvement']:.1f}%")
        print(f"   Total LLM Matches: {overall_perf['total_llm_matches']}")
        print(f"   Improvement Ratio: {overall_perf['improvement_ratio']:.2f}x")
        
        matching_quality = evaluation['matching_quality']
        print(f"   Average Confidence: {matching_quality['average_confidence']:.2f}")
        print(f"   High Confidence Matches: {matching_quality['high_confidence_matches']}")
        print(f"   Low Confidence Matches: {matching_quality['low_confidence_matches']}")
        print(f"   Average Reasoning Quality: {matching_quality['average_reasoning_quality']:.2f}")
        
        success_metrics = evaluation['success_metrics']
        print(f"   Prompt Effectiveness Score: {success_metrics['prompt_effectiveness_score']:.2f}")
        print(f"   Overall Assessment: {success_metrics['overall_assessment']}")
        
        # Prompt issues
        if evaluation['prompt_issues']:
            print(f"\n⚠️  PROMPT ISSUES IDENTIFIED:")
            for i, issue in enumerate(evaluation['prompt_issues'], 1):
                print(f"   {i}. {issue}")
        
        # Recommendations
        print(f"\n💡 PROMPT IMPROVEMENT RECOMMENDATIONS:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "="*80)
    
    def save_test_results(self, results: Dict[str, Any], output_path: str):
        """Save comprehensive test results."""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✅ Comprehensive test results saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving test results: {e}")


def main():
    """Main function to run comprehensive LLM matching test."""
    print("🚀 Comprehensive LLM Matching Test")
    print("Testing prompt effectiveness across all document types")
    print("=" * 60)
    
    # Template path
    template_path = "c8500_superset_template.json"
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        print("   Run llm_superset_template_generator.py first to create the template")
        return
    
    # Initialize test
    test = ComprehensiveLLMMatchingTest(template_path)
    
    # Run comprehensive test
    results = test.test_all_documents()
    
    # Print results
    test.print_comprehensive_results(results)
    
    # Save results
    output_path = "comprehensive_llm_matching_test_results.json"
    test.save_test_results(results, output_path)
    
    print(f"\n🎯 Comprehensive LLM matching test complete!")
    print(f"   Results: {output_path}")
    print(f"   Review the prompt evaluation to determine if improvements are needed")


if __name__ == "__main__":
    main() 