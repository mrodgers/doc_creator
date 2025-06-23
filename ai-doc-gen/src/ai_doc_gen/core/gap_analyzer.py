#!/usr/bin/env python3
"""
Gap Analysis Engine
Identifies missing documentation sections and generates actionable gap reports with SME query suggestions.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from ..utils.llm import LLMUtility

logger = logging.getLogger(__name__)


@dataclass
class GapItem:
    """Represents a specific gap in documentation."""
    id: str
    template_section: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str
    description: str
    impact: str
    suggested_content: str
    priority: int
    source: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SMEQuery:
    """Represents a question for Subject Matter Experts."""
    id: str
    gap_id: str
    question: str
    context: str
    priority: int
    expected_answer_type: str  # 'technical_spec', 'procedure', 'requirement', 'clarification'
    related_sections: List[str] = None
    
    def __post_init__(self):
        if self.related_sections is None:
            self.related_sections = []


@dataclass
class GapReport:
    """Complete gap analysis report."""
    document_title: str
    gaps: List[GapItem]
    sme_queries: List[SMEQuery]
    coverage_percentage: float
    critical_gaps: int
    high_priority_gaps: int
    total_gaps: int
    generated_at: str
    recommendations: List[str]


class GapAnalyzer:
    """Analyzes documentation gaps and generates SME queries."""
    
    def __init__(self, llm_utility: Optional[LLMUtility] = None):
        self.llm_utility = llm_utility or LLMUtility()
        self.template_sections = self._load_template_sections()
        
    def _load_template_sections(self) -> List[Dict[str, Any]]:
        """Load template sections for gap analysis."""
        return [
            {
                "id": "hardware_overview",
                "title": "Hardware Overview",
                "category": "hardware",
                "severity": "critical",
                "description": "Overview of hardware components, specifications, and features",
                "impact": "Critical for understanding system capabilities and requirements"
            },
            {
                "id": "installation_preparation",
                "title": "Installation Preparation",
                "category": "preparation",
                "severity": "critical",
                "description": "Pre-installation requirements, tools, and safety considerations",
                "impact": "Essential for safe and successful installation"
            },
            {
                "id": "hardware_installation",
                "title": "Hardware Installation",
                "category": "installation",
                "severity": "critical",
                "description": "Step-by-step hardware installation procedures",
                "impact": "Core installation process documentation"
            },
            {
                "id": "initial_configuration",
                "title": "Initial Configuration",
                "category": "configuration",
                "severity": "high",
                "description": "Basic configuration and setup procedures",
                "impact": "Required for system operation"
            },
            {
                "id": "advanced_configuration",
                "title": "Advanced Configuration",
                "category": "configuration",
                "severity": "medium",
                "description": "Advanced configuration options and features",
                "impact": "Important for optimal system performance"
            },
            {
                "id": "verification_testing",
                "title": "Verification and Testing",
                "category": "testing",
                "severity": "high",
                "description": "Verification procedures and testing guidelines",
                "impact": "Critical for ensuring proper installation and operation"
            },
            {
                "id": "troubleshooting",
                "title": "Troubleshooting",
                "category": "troubleshooting",
                "severity": "medium",
                "description": "Common issues and troubleshooting procedures",
                "impact": "Important for maintenance and support"
            },
            {
                "id": "maintenance",
                "title": "Maintenance and Support",
                "category": "maintenance",
                "severity": "low",
                "description": "Maintenance procedures and support information",
                "impact": "Useful for ongoing system maintenance"
            }
        ]
    
    def analyze_gaps(self, existing_sections: List[str], document_title: str) -> GapReport:
        """Analyze gaps in documentation coverage."""
        logger.info(f"Analyzing gaps for: {document_title}")
        
        # Identify missing sections
        gaps = self._identify_missing_sections(existing_sections)
        
        # Generate SME queries for gaps
        sme_queries = self._generate_sme_queries(gaps, document_title)
        
        # Calculate metrics
        coverage_percentage = self._calculate_coverage(existing_sections)
        critical_gaps = len([g for g in gaps if g.severity == 'critical'])
        high_priority_gaps = len([g for g in gaps if g.severity in ['critical', 'high']])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, coverage_percentage)
        
        report = GapReport(
            document_title=document_title,
            gaps=gaps,
            sme_queries=sme_queries,
            coverage_percentage=coverage_percentage,
            critical_gaps=critical_gaps,
            high_priority_gaps=high_priority_gaps,
            total_gaps=len(gaps),
            generated_at=datetime.now().isoformat(),
            recommendations=recommendations
        )
        
        logger.info(f"Gap analysis completed: {len(gaps)} gaps, {len(sme_queries)} SME queries")
        
        return report
    
    def _identify_missing_sections(self, existing_sections: List[str]) -> List[GapItem]:
        """Identify missing sections based on template."""
        gaps = []
        
        for template in self.template_sections:
            if template['id'] not in existing_sections:
                gap = GapItem(
                    id=f"gap_{template['id']}",
                    template_section=template['title'],
                    severity=template['severity'],
                    category=template['category'],
                    description=template['description'],
                    impact=template['impact'],
                    suggested_content=self._generate_suggested_content(template),
                    priority=self._calculate_priority(template['severity']),
                    source="gap_analyzer"
                )
                gaps.append(gap)
        
        return gaps
    
    def _calculate_priority(self, severity: str) -> int:
        """Calculate priority based on severity."""
        priority_map = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        return priority_map.get(severity, 3)
    
    def _generate_suggested_content(self, template: Dict[str, Any]) -> str:
        """Generate suggested content for a gap."""
        return f"Content needed for {template['title']} section. This should include {template['description'].lower()}."
    
    def _generate_sme_queries(self, gaps: List[GapItem], document_title: str) -> List[SMEQuery]:
        """Generate SME queries for identified gaps."""
        sme_queries = []
        
        for gap in gaps:
            # Generate multiple queries per gap
            queries = self._generate_queries_for_gap(gap, document_title)
            sme_queries.extend(queries)
        
        return sme_queries
    
    def _generate_queries_for_gap(self, gap: GapItem, document_title: str) -> List[SMEQuery]:
        """Generate specific queries for a gap."""
        queries = []
        
        # Base query for the gap
        base_query = SMEQuery(
            id=f"query_{gap.id}",
            gap_id=gap.id,
            question=f"What specific content should be included in the '{gap.template_section}' section?",
            context=f"Document: {document_title}, Gap: {gap.description}",
            priority=gap.priority,
            expected_answer_type="technical_spec",
            related_sections=[gap.template_section]
        )
        queries.append(base_query)
        
        # Additional context-specific queries
        if gap.category == "hardware":
            queries.append(SMEQuery(
                id=f"query_{gap.id}_specs",
                gap_id=gap.id,
                question=f"What are the key hardware specifications and requirements for {document_title}?",
                context=f"Document: {document_title}, Section: {gap.template_section}",
                priority=gap.priority,
                expected_answer_type="technical_spec",
                related_sections=[gap.template_section]
            ))
        
        elif gap.category == "installation":
            queries.append(SMEQuery(
                id=f"query_{gap.id}_procedure",
                gap_id=gap.id,
                question=f"What are the step-by-step procedures for {gap.template_section.lower()}?",
                context=f"Document: {document_title}, Section: {gap.template_section}",
                priority=gap.priority,
                expected_answer_type="procedure",
                related_sections=[gap.template_section]
            ))
        
        elif gap.category == "configuration":
            queries.append(SMEQuery(
                id=f"query_{gap.id}_config",
                gap_id=gap.id,
                question=f"What configuration parameters and settings are required for {gap.template_section.lower()}?",
                context=f"Document: {document_title}, Section: {gap.template_section}",
                priority=gap.priority,
                expected_answer_type="technical_spec",
                related_sections=[gap.template_section]
            ))
        
        return queries
    
    def _calculate_coverage(self, existing_sections: List[str]) -> float:
        """Calculate coverage percentage."""
        total_sections = len(self.template_sections)
        covered_sections = len(existing_sections)
        return (covered_sections / total_sections) * 100 if total_sections > 0 else 0
    
    def _generate_recommendations(self, gaps: List[GapItem], coverage_percentage: float) -> List[str]:
        """Generate recommendations based on gap analysis."""
        recommendations = []
        
        # Coverage-based recommendations
        if coverage_percentage < 50:
            recommendations.append("Documentation coverage is critically low. Focus on essential sections first.")
        elif coverage_percentage < 75:
            recommendations.append("Documentation coverage needs improvement. Prioritize high-severity gaps.")
        else:
            recommendations.append("Documentation coverage is good. Focus on remaining gaps for completeness.")
        
        # Severity-based recommendations
        critical_gaps = [g for g in gaps if g.severity == 'critical']
        if critical_gaps:
            recommendations.append(f"Address {len(critical_gaps)} critical gaps immediately for basic documentation completeness.")
        
        high_gaps = [g for g in gaps if g.severity == 'high']
        if high_gaps:
            recommendations.append(f"Prioritize {len(high_gaps)} high-priority gaps for comprehensive coverage.")
        
        # Category-based recommendations
        categories = set(g.category for g in gaps)
        if 'hardware' in categories:
            recommendations.append("Hardware documentation gaps should be addressed first for installation readiness.")
        if 'installation' in categories:
            recommendations.append("Installation procedure gaps are critical for successful deployment.")
        if 'configuration' in categories:
            recommendations.append("Configuration gaps should be filled for operational readiness.")
        
        return recommendations
    
    def generate_llm_enhanced_queries(self, gaps: List[GapItem], document_title: str) -> List[SMEQuery]:
        """Generate LLM-enhanced SME queries."""
        enhanced_queries = []
        
        for gap in gaps:
            try:
                # Use LLM to generate enhanced queries
                prompt = f"""
Generate 2-3 specific, actionable questions for a Subject Matter Expert about this documentation gap:

Document: {document_title}
Missing Section: {gap.template_section}
Category: {gap.category}
Description: {gap.description}
Impact: {gap.impact}

Generate questions that will help fill this gap with accurate, detailed content.
Focus on technical specifications, procedures, requirements, or clarifications needed.

Return as a JSON array of questions with this structure:
[
  {{
    "question": "Specific question text",
    "context": "Additional context",
    "answer_type": "technical_spec|procedure|requirement|clarification"
  }}
]
"""
                
                response = self.llm_utility.get_synonyms_from_llm(prompt)
                if response and isinstance(response, list):
                    for i, query_data in enumerate(response):
                        if isinstance(query_data, dict):
                            enhanced_query = SMEQuery(
                                id=f"llm_query_{gap.id}_{i}",
                                gap_id=gap.id,
                                question=query_data.get('question', ''),
                                context=query_data.get('context', ''),
                                priority=gap.priority,
                                expected_answer_type=query_data.get('answer_type', 'clarification'),
                                related_sections=[gap.template_section]
                            )
                            enhanced_queries.append(enhanced_query)
                
            except Exception as e:
                logger.warning(f"Failed to generate LLM-enhanced query for gap {gap.id}: {e}")
                # Fallback to basic query
                enhanced_queries.append(SMEQuery(
                    id=f"fallback_query_{gap.id}",
                    gap_id=gap.id,
                    question=f"What content is needed for the '{gap.template_section}' section?",
                    context=f"Document: {document_title}",
                    priority=gap.priority,
                    expected_answer_type="clarification",
                    related_sections=[gap.template_section]
                ))
        
        return enhanced_queries
    
    def save_gap_report(self, report: GapReport, output_path: str):
        """Save gap report to file."""
        output_data = asdict(report)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Gap report saved to: {output_path}")
    
    def export_gap_report_markdown(self, report: GapReport, output_path: str):
        """Export gap report as Markdown."""
        markdown_content = []
        
        # Header
        markdown_content.append(f"# Gap Analysis Report: {report.document_title}")
        markdown_content.append("")
        markdown_content.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        markdown_content.append(f"*Coverage: {report.coverage_percentage:.1f}%*")
        markdown_content.append(f"*Total Gaps: {report.total_gaps}*")
        markdown_content.append(f"*Critical Gaps: {report.critical_gaps}*")
        markdown_content.append("")
        
        # Executive Summary
        markdown_content.append("## Executive Summary")
        markdown_content.append("")
        markdown_content.append(f"This document identifies {report.total_gaps} gaps in the {report.document_title} documentation.")
        markdown_content.append(f"Current coverage is {report.coverage_percentage:.1f}% with {report.critical_gaps} critical gaps requiring immediate attention.")
        markdown_content.append("")
        
        # Recommendations
        markdown_content.append("## Recommendations")
        markdown_content.append("")
        for rec in report.recommendations:
            markdown_content.append(f"- {rec}")
        markdown_content.append("")
        
        # Gaps
        markdown_content.append("## Documentation Gaps")
        markdown_content.append("")
        
        for gap in sorted(report.gaps, key=lambda x: x.priority):
            markdown_content.append(f"### {gap.template_section}")
            markdown_content.append(f"**Severity:** {gap.severity}")
            markdown_content.append(f"**Category:** {gap.category}")
            markdown_content.append(f"**Priority:** {gap.priority}")
            markdown_content.append(f"**Impact:** {gap.impact}")
            markdown_content.append(f"**Description:** {gap.description}")
            markdown_content.append(f"**Suggested Content:** {gap.suggested_content}")
            markdown_content.append("")
        
        # SME Queries
        markdown_content.append("## SME Queries")
        markdown_content.append("")
        markdown_content.append("The following questions should be addressed by Subject Matter Experts:")
        markdown_content.append("")
        
        for query in sorted(report.sme_queries, key=lambda x: x.priority):
            markdown_content.append(f"### {query.question}")
            markdown_content.append(f"**Priority:** {query.priority}")
            markdown_content.append(f"**Context:** {query.context}")
            markdown_content.append(f"**Expected Answer Type:** {query.expected_answer_type}")
            markdown_content.append("")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(markdown_content))
        
        logger.info(f"Gap report exported to: {output_path}")


def main():
    """Test the gap analyzer."""
    # Test with some existing sections
    existing_sections = ["hardware_overview", "installation_preparation"]
    
    # Initialize analyzer
    analyzer = GapAnalyzer()
    
    # Analyze gaps
    report = analyzer.analyze_gaps(existing_sections, "Cisco Nexus 9000 Installation Guide")
    
    # Save results
    analyzer.save_gap_report(report, "test_gap_report.json")
    analyzer.export_gap_report_markdown(report, "test_gap_report.md")
    
    print(f"✅ Gap analysis completed!")
    print(f"   Coverage: {report.coverage_percentage:.1f}%")
    print(f"   Total gaps: {report.total_gaps}")
    print(f"   Critical gaps: {report.critical_gaps}")
    print(f"   SME queries: {len(report.sme_queries)}")


if __name__ == "__main__":
    main()
