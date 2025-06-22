#!/usr/bin/env python3
"""
Test Adaptive LLM Evolution

This script demonstrates the step-by-step approach of the adaptive LLM matcher:
1. Initial LLM matching
2. Self-evaluation
3. Prompt improvement suggestions
4. Prompt evolution
5. Re-running with evolved prompt
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from adaptive_llm_matcher import AdaptiveLLMMatcher


class AdaptiveEvolutionTest:
    """Test class for demonstrating adaptive LLM evolution."""

    def __init__(self, template_path: str):
        self.template_path = template_path
        self.matcher = AdaptiveLLMMatcher(template_path)

    def test_evolution_cycle(self, document_path: str) -> Dict[str, Any]:
        """Test a complete evolution cycle."""
        print("🧪 TESTING ADAPTIVE EVOLUTION CYCLE")
        print(f"Document: {document_path}")
        print("=" * 60)

        # Run adaptive analysis
        results = self.matcher.analyze_document_adaptive(document_path)

        # Analyze evolution
        evolution_analysis = self._analyze_evolution(results)

        # Compile test results
        test_results = {
            'test_info': {
                'document': document_path,
                'template': self.template_path,
                'timestamp': datetime.now().isoformat(),
                'evolution_cycle': 'complete'
            },
            'results': results,
            'evolution_analysis': evolution_analysis,
            'recommendations': self._generate_recommendations(results, evolution_analysis)
        }

        return test_results

    def _analyze_evolution(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the evolution process."""
        evolution = results.get('prompt_evolution', {})
        evaluation = results.get('evaluation', {})
        improvements = results.get('improvements', {})

        analysis = {
            'evolution_occurred': evolution.get('evolved_this_run', False),
            'total_evolutions': evolution.get('total_evolutions', 0),
            'current_version': evolution.get('current_version', '1.0'),
            'performance_metrics': {
                'initial_score': evaluation.get('overall_score', 0),
                'confidence_issues': len(evaluation.get('confidence_issues', [])),
                'reasoning_issues': len(evaluation.get('reasoning_issues', [])),
                'coverage_issues': len(evaluation.get('coverage_issues', []))
            },
            'improvement_suggestions': {
                'total_suggestions': len(improvements.get('suggestions', [])),
                'high_priority': len([s for s in improvements.get('suggestions', [])
                                   if s.get('priority') == 'high']),
                'medium_priority': len([s for s in improvements.get('suggestions', [])
                                     if s.get('priority') == 'medium']),
                'low_priority': len([s for s in improvements.get('suggestions', [])
                                   if s.get('priority') == 'low'])
            },
            'evolution_effectiveness': self._assess_evolution_effectiveness(results)
        }

        return analysis

    def _assess_evolution_effectiveness(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how effective the evolution was."""
        matching = results.get('matching_results', {})
        evaluation = results.get('evaluation', {})
        evolution = results.get('prompt_evolution', {})

        effectiveness = {
            'coverage_improvement': matching.get('coverage_percentage', 0),
            'match_quality': len(matching.get('matches', [])),
            'overall_score': evaluation.get('overall_score', 0),
            'evolution_success': evolution.get('evolved_this_run', False),
            'suggestions_implemented': len(evolution.get('changes', [])) if evolution.get('evolved_this_run') else 0
        }

        # Calculate effectiveness score
        score = 0.0

        # Coverage factor (30%)
        coverage = effectiveness['coverage_improvement']
        score += min(coverage / 50, 1.0) * 0.3  # Normalize to 50% coverage

        # Match quality factor (25%)
        match_count = effectiveness['match_quality']
        score += min(match_count / 10, 1.0) * 0.25  # Normalize to 10 matches

        # Overall score factor (25%)
        overall_score = effectiveness['overall_score']
        score += (overall_score / 100) * 0.25

        # Evolution success factor (20%)
        if effectiveness['evolution_success']:
            score += 0.2

        effectiveness['effectiveness_score'] = min(score, 1.0)
        effectiveness['effectiveness_level'] = self._get_effectiveness_level(score)

        return effectiveness

    def _get_effectiveness_level(self, score: float) -> str:
        """Get effectiveness level based on score."""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"

    def _generate_recommendations(self, results: Dict[str, Any], evolution_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evolution analysis."""
        recommendations = []

        effectiveness = evolution_analysis.get('evolution_effectiveness', {})
        effectiveness_score = effectiveness.get('effectiveness_score', 0)

        # Performance-based recommendations
        if effectiveness_score < 0.4:
            recommendations.append("Consider redesigning the base prompt with more specific technical domain examples")

        if effectiveness['coverage_improvement'] < 10:
            recommendations.append("Increase prompt specificity for better section matching")

        if effectiveness['match_quality'] < 5:
            recommendations.append("Add more detailed matching criteria and examples to the prompt")

        # Evolution-based recommendations
        if not effectiveness['evolution_success']:
            recommendations.append("Enable prompt evolution for continuous improvement")

        if effectiveness['suggestions_implemented'] < 3:
            recommendations.append("Implement more improvement suggestions in the evolution process")

        # Success-based recommendations
        if effectiveness_score >= 0.8:
            recommendations.append("Evolution is working well - consider fine-tuning for edge cases")
        elif effectiveness_score >= 0.6:
            recommendations.append("Evolution shows promise - focus on improving coverage and match quality")
        else:
            recommendations.append("Significant improvements needed - consider complete prompt redesign")

        return recommendations

    def test_multiple_evolution_cycles(self, documents: List[str]) -> Dict[str, Any]:
        """Test multiple evolution cycles to see how prompts improve over time."""
        print("🔄 TESTING MULTIPLE EVOLUTION CYCLES")
        print(f"Documents: {len(documents)}")
        print("=" * 60)

        cycle_results = []
        evolution_tracking = {
            'prompt_versions': [],
            'performance_trends': [],
            'improvement_patterns': []
        }

        for i, doc_path in enumerate(documents, 1):
            print(f"\n📄 Cycle {i}: {doc_path}")

            # Run evolution cycle
            cycle_result = self.test_evolution_cycle(doc_path)
            cycle_results.append(cycle_result)

            # Track evolution
            evolution = cycle_result['results'].get('prompt_evolution', {})
            evaluation = cycle_result['results'].get('evaluation', {})

            evolution_tracking['prompt_versions'].append({
                'cycle': i,
                'version': evolution.get('current_version', '1.0'),
                'evolved': evolution.get('evolved_this_run', False)
            })

            evolution_tracking['performance_trends'].append({
                'cycle': i,
                'overall_score': evaluation.get('overall_score', 0),
                'coverage': cycle_result['results'].get('matching_results', {}).get('coverage_percentage', 0),
                'matches': cycle_result['results'].get('matching_results', {}).get('matches_count', 0)
            })

            # Track improvement patterns
            improvements = cycle_result['results'].get('improvements', {})
            evolution_tracking['improvement_patterns'].append({
                'cycle': i,
                'suggestions_count': len(improvements.get('suggestions', [])),
                'high_priority_count': len([s for s in improvements.get('suggestions', [])
                                         if s.get('priority') == 'high']),
                'should_evolve': improvements.get('should_evolve', False)
            })

        # Analyze trends
        trend_analysis = self._analyze_evolution_trends(evolution_tracking)

        return {
            'test_info': {
                'total_cycles': len(documents),
                'documents': documents,
                'timestamp': datetime.now().isoformat()
            },
            'cycle_results': cycle_results,
            'evolution_tracking': evolution_tracking,
            'trend_analysis': trend_analysis,
            'overall_assessment': self._assess_overall_evolution(cycle_results, trend_analysis)
        }

    def _analyze_evolution_trends(self, evolution_tracking: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends across multiple evolution cycles."""
        performance_trends = evolution_tracking['performance_trends']

        if len(performance_trends) < 2:
            return {'trend': 'insufficient_data', 'improvement_rate': 0}

        # Calculate improvement trends
        scores = [p['overall_score'] for p in performance_trends]
        coverages = [p['coverage'] for p in performance_trends]
        matches = [p['matches'] for p in performance_trends]

        # Score trend
        score_improvement = (scores[-1] - scores[0]) / len(scores) if len(scores) > 1 else 0

        # Coverage trend
        coverage_improvement = (coverages[-1] - coverages[0]) / len(coverages) if len(coverages) > 1 else 0

        # Match quality trend
        match_improvement = (matches[-1] - matches[0]) / len(matches) if len(matches) > 1 else 0

        # Evolution frequency
        evolution_frequency = sum(1 for v in evolution_tracking['prompt_versions'] if v['evolved']) / len(evolution_tracking['prompt_versions'])

        return {
            'score_trend': {
                'improvement_rate': score_improvement,
                'trend_direction': 'improving' if score_improvement > 0 else 'declining' if score_improvement < 0 else 'stable'
            },
            'coverage_trend': {
                'improvement_rate': coverage_improvement,
                'trend_direction': 'improving' if coverage_improvement > 0 else 'declining' if coverage_improvement < 0 else 'stable'
            },
            'match_quality_trend': {
                'improvement_rate': match_improvement,
                'trend_direction': 'improving' if match_improvement > 0 else 'declining' if match_improvement < 0 else 'stable'
            },
            'evolution_frequency': evolution_frequency,
            'overall_trend': self._determine_overall_trend(score_improvement, coverage_improvement, match_improvement)
        }

    def _determine_overall_trend(self, score_improvement: float, coverage_improvement: float, match_improvement: float) -> str:
        """Determine overall trend based on all metrics."""
        positive_metrics = sum(1 for improvement in [score_improvement, coverage_improvement, match_improvement] if improvement > 0)

        if positive_metrics >= 2:
            return "improving"
        elif positive_metrics == 1:
            return "mixed"
        else:
            return "declining"

    def _assess_overall_evolution(self, cycle_results: List[Dict[str, Any]], trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall evolution effectiveness."""
        # Calculate average effectiveness across cycles
        effectiveness_scores = []
        for cycle_result in cycle_results:
            effectiveness = cycle_result['evolution_analysis']['evolution_effectiveness']
            effectiveness_scores.append(effectiveness['effectiveness_score'])

        avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0

        # Assess evolution success
        evolution_success_rate = trend_analysis.get('evolution_frequency', 0)

        # Determine overall assessment
        if avg_effectiveness >= 0.7 and trend_analysis.get('overall_trend') == 'improving':
            overall_assessment = "Excellent"
        elif avg_effectiveness >= 0.5 and trend_analysis.get('overall_trend') != 'declining':
            overall_assessment = "Good"
        elif avg_effectiveness >= 0.3:
            overall_assessment = "Fair"
        else:
            overall_assessment = "Poor"

        return {
            'average_effectiveness': avg_effectiveness,
            'evolution_success_rate': evolution_success_rate,
            'overall_assessment': overall_assessment,
            'recommendations': self._generate_overall_recommendations(avg_effectiveness, trend_analysis)
        }

    def _generate_overall_recommendations(self, avg_effectiveness: float, trend_analysis: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations based on evolution performance."""
        recommendations = []

        if avg_effectiveness < 0.5:
            recommendations.append("Consider fundamental prompt redesign with more technical specificity")

        if trend_analysis.get('overall_trend') == 'declining':
            recommendations.append("Investigate why performance is declining and adjust evolution strategy")

        if trend_analysis.get('evolution_frequency', 0) < 0.5:
            recommendations.append("Increase evolution frequency by lowering improvement thresholds")

        if trend_analysis.get('score_trend', {}).get('improvement_rate', 0) < 5:
            recommendations.append("Focus on improving self-evaluation accuracy and prompt suggestions")

        return recommendations

    def print_evolution_test_results(self, test_results: Dict[str, Any]):
        """Print comprehensive evolution test results."""
        print("\n" + "="*80)
        print("🔄 ADAPTIVE EVOLUTION TEST RESULTS")
        print("="*80)

        # Test info
        test_info = test_results['test_info']
        print("\n📋 TEST INFORMATION:")
        print(f"   Document: {test_info['document']}")
        print(f"   Template: {test_info['template']}")
        print(f"   Timestamp: {test_info['timestamp']}")

        # Evolution analysis
        evolution_analysis = test_results['evolution_analysis']
        print("\n📊 EVOLUTION ANALYSIS:")
        print(f"   Evolution Occurred: {evolution_analysis['evolution_occurred']}")
        print(f"   Total Evolutions: {evolution_analysis['total_evolutions']}")
        print(f"   Current Version: {evolution_analysis['current_version']}")

        # Performance metrics
        performance = evolution_analysis['performance_metrics']
        print(f"   Initial Score: {performance['initial_score']:.1f}/100")
        print(f"   Confidence Issues: {performance['confidence_issues']}")
        print(f"   Reasoning Issues: {performance['reasoning_issues']}")
        print(f"   Coverage Issues: {performance['coverage_issues']}")

        # Improvement suggestions
        suggestions = evolution_analysis['improvement_suggestions']
        print("\n💡 IMPROVEMENT SUGGESTIONS:")
        print(f"   Total Suggestions: {suggestions['total_suggestions']}")
        print(f"   High Priority: {suggestions['high_priority']}")
        print(f"   Medium Priority: {suggestions['medium_priority']}")
        print(f"   Low Priority: {suggestions['low_priority']}")

        # Evolution effectiveness
        effectiveness = evolution_analysis['evolution_effectiveness']
        print("\n🎯 EVOLUTION EFFECTIVENESS:")
        print(f"   Effectiveness Score: {effectiveness['effectiveness_score']:.2f}")
        print(f"   Effectiveness Level: {effectiveness['effectiveness_level']}")
        print(f"   Coverage: {effectiveness['coverage_improvement']:.1f}%")
        print(f"   Match Quality: {effectiveness['match_quality']}")

        # Recommendations
        recommendations = test_results['recommendations']
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

        print("\n" + "="*80)

    def save_evolution_test_results(self, test_results: Dict[str, Any], output_path: str):
        """Save evolution test results."""
        try:
            with open(output_path, 'w') as f:
                json.dump(test_results, f, indent=2, default=str)
            print(f"✅ Evolution test results saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


def main():
    """Main function to demonstrate adaptive evolution testing."""
    print("🚀 Adaptive LLM Evolution Test")
    print("=" * 60)

    # Template path
    template_path = "c8500_superset_template.json"
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        print("   Run llm_superset_template_generator.py first to create the template")
        return

    # Initialize test
    test = AdaptiveEvolutionTest(template_path)

    # Test documents
    test_docs = ["functional_spec.docx"]

    # Add more documents if available
    if Path("installation_guide.pdf").exists():
        test_docs.append("installation_guide.pdf")

    if Path("cisco_nexus_llm_test.html").exists():
        test_docs.append("cisco_nexus_llm_test.html")

    print(f"📄 Testing with {len(test_docs)} documents: {test_docs}")

    # Run single evolution cycle test
    print("\n🧪 SINGLE EVOLUTION CYCLE TEST")
    single_results = test.test_evolution_cycle(test_docs[0])
    test.print_evolution_test_results(single_results)

    # Save single cycle results
    single_output = "single_evolution_cycle_results.json"
    test.save_evolution_test_results(single_results, single_output)

    # Run multiple evolution cycles test if multiple documents
    if len(test_docs) > 1:
        print("\n🔄 MULTIPLE EVOLUTION CYCLES TEST")
        multiple_results = test.test_multiple_evolution_cycles(test_docs)

        # Print multiple cycles summary
        print("\n📊 MULTIPLE CYCLES SUMMARY:")
        overall = multiple_results['overall_assessment']
        print(f"   Average Effectiveness: {overall['average_effectiveness']:.2f}")
        print(f"   Evolution Success Rate: {overall['evolution_success_rate']:.1%}")
        print(f"   Overall Assessment: {overall['overall_assessment']}")

        # Save multiple cycles results
        multiple_output = "multiple_evolution_cycles_results.json"
        test.save_evolution_test_results(multiple_results, multiple_output)

    print("\n🎯 Adaptive evolution test complete!")
    print(f"   Single Cycle Results: {single_output}")
    if len(test_docs) > 1:
        print(f"   Multiple Cycles Results: {multiple_output}")
    print("   Prompt History: adaptive_prompt_history.json")


if __name__ == "__main__":
    main()
