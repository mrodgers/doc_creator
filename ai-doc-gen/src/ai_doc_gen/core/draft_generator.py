#!/usr/bin/env python3
"""
Core Draft Generation Module
Generates documentation drafts using proven matching capabilities with provenance tracking.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from ..utils.llm import LLMUtility
from ..utils.acronym_expander import AcronymExpander

logger = logging.getLogger(__name__)


@dataclass
class ContentSection:
    """Represents a section of content with metadata."""
    id: str
    title: str
    content: str
    source: str
    confidence: float
    template_match: Optional[str] = None
    synonyms: List[str] = None
    acronyms_found: List[Tuple[str, str]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.synonyms is None:
            self.synonyms = []
        if self.acronyms_found is None:
            self.acronyms_found = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class DraftSection:
    """Represents a generated draft section."""
    template_id: str
    template_title: str
    content: str
    confidence: float
    source_sections: List[str]
    provenance: Dict[str, Any]
    generated_at: str
    word_count: int = 0
    
    def __post_init__(self):
        if self.word_count == 0:
            self.word_count = len(self.content.split())


@dataclass
class GapAnalysis:
    """Represents a gap in documentation coverage."""
    template_section: str
    severity: str  # 'high', 'medium', 'low'
    description: str
    suggested_content: str
    priority: int
    source: str


@dataclass
class DraftResult:
    """Complete draft generation result."""
    document_title: str
    sections: List[DraftSection]
    gaps: List[GapAnalysis]
    coverage_percentage: float
    total_word_count: int
    generation_time: float
    provenance_summary: Dict[str, Any]
    confidence_score: float


class DraftGenerator:
    """Generates documentation drafts using proven matching capabilities."""
    
    def __init__(self, llm_utility: Optional[LLMUtility] = None, 
                 acronym_expander: Optional[AcronymExpander] = None):
        self.llm_utility = llm_utility or LLMUtility()
        self.acronym_expander = acronym_expander or AcronymExpander()
        self.template_sections = self._load_template_sections()
        
    def _load_template_sections(self) -> List[Dict[str, Any]]:
        """Load template sections for documentation generation."""
        return [
            {
                "id": "hardware_overview",
                "title": "Hardware Overview",
                "content": "Overview of hardware components, specifications, and features",
                "category": "hardware",
                "priority": "high",
                "required": True
            },
            {
                "id": "installation_preparation",
                "title": "Installation Preparation",
                "content": "Pre-installation requirements, tools, and safety considerations",
                "category": "preparation",
                "priority": "high",
                "required": True
            },
            {
                "id": "hardware_installation",
                "title": "Hardware Installation",
                "content": "Step-by-step hardware installation procedures",
                "category": "installation",
                "priority": "high",
                "required": True
            },
            {
                "id": "initial_configuration",
                "title": "Initial Configuration",
                "content": "Basic configuration and setup procedures",
                "category": "configuration",
                "priority": "high",
                "required": True
            },
            {
                "id": "advanced_configuration",
                "title": "Advanced Configuration",
                "content": "Advanced configuration options and features",
                "category": "configuration",
                "priority": "medium",
                "required": False
            },
            {
                "id": "verification_testing",
                "title": "Verification and Testing",
                "content": "Verification procedures and testing guidelines",
                "category": "testing",
                "priority": "medium",
                "required": True
            },
            {
                "id": "troubleshooting",
                "title": "Troubleshooting",
                "content": "Common issues and troubleshooting procedures",
                "category": "troubleshooting",
                "priority": "medium",
                "required": False
            },
            {
                "id": "maintenance",
                "title": "Maintenance and Support",
                "content": "Maintenance procedures and support information",
                "category": "maintenance",
                "priority": "low",
                "required": False
            }
        ]
    
    def generate_draft(self, content_sections: List[ContentSection], 
                      document_title: str) -> DraftResult:
        """Generate a complete documentation draft."""
        start_time = time.time()
        
        logger.info(f"Generating draft for: {document_title}")
        logger.info(f"Processing {len(content_sections)} content sections")
        
        # Step 1: Match content sections to templates
        matched_sections = self._match_content_to_templates(content_sections)
        
        # Step 2: Generate draft sections
        draft_sections = self._generate_draft_sections(matched_sections)
        
        # Step 3: Analyze gaps
        gaps = self._analyze_gaps(draft_sections)
        
        # Step 4: Calculate metrics
        coverage_percentage = self._calculate_coverage(draft_sections)
        total_word_count = sum(section.word_count for section in draft_sections)
        confidence_score = self._calculate_confidence(draft_sections)
        
        # Step 5: Compile provenance
        provenance_summary = self._compile_provenance(content_sections, draft_sections)
        
        generation_time = time.time() - start_time
        
        result = DraftResult(
            document_title=document_title,
            sections=draft_sections,
            gaps=gaps,
            coverage_percentage=coverage_percentage,
            total_word_count=total_word_count,
            generation_time=generation_time,
            provenance_summary=provenance_summary,
            confidence_score=confidence_score
        )
        
        logger.info(f"Draft generation completed in {generation_time:.2f}s")
        logger.info(f"Coverage: {coverage_percentage:.1f}%, Confidence: {confidence_score:.2f}")
        
        return result
    
    def _match_content_to_templates(self, content_sections: List[ContentSection]) -> Dict[str, List[ContentSection]]:
        """Match content sections to template sections."""
        matched_sections = {template['id']: [] for template in self.template_sections}
        
        for section in content_sections:
            # Find best template match
            best_match = self._find_best_template_match(section)
            if best_match:
                matched_sections[best_match].append(section)
        
        return matched_sections
    
    def _find_best_template_match(self, section: ContentSection) -> Optional[str]:
        """Find the best template match for a content section."""
        best_match = None
        best_score = 0.0
        
        for template in self.template_sections:
            score = self._calculate_match_score(section, template)
            if score > best_score and score > 0.3:  # Minimum threshold
                best_score = score
                best_match = template['id']
        
        return best_match
    
    def _calculate_match_score(self, section: ContentSection, template: Dict[str, Any]) -> float:
        """Calculate match score between content section and template using synonyms and acronyms."""
        # Gather base keywords
        template_keywords = set(template['title'].lower().split() + template['content'].lower().split())
        section_keywords = set(section.title.lower().split() + section.content.lower().split())

        # Expand with synonyms (LLMUtility)
        template_synonyms = set()
        section_synonyms = set()
        try:
            template_synonyms.update(self.llm_utility.get_synonyms_from_llm(template['title']))
            section_synonyms.update(self.llm_utility.get_synonyms_from_llm(section.title))
        except Exception as e:
            logger.warning(f"Synonym expansion failed: {e}")

        # Expand with acronyms (AcronymExpander)
        template_acronyms = set(self.acronym_expander.get_acronym_synonyms(template['title']))
        section_acronyms = set(self.acronym_expander.get_acronym_synonyms(section.title))

        # Combine all
        template_all = template_keywords | template_synonyms | template_acronyms
        section_all = section_keywords | section_synonyms | section_acronyms

        # Calculate intersection
        intersection = template_all.intersection(section_all)
        if not template_all:
            return 0.0
        # Jaccard similarity
        similarity = len(intersection) / len(template_all.union(section_all))
        # Boost score based on confidence
        boosted_score = similarity * (0.5 + 0.5 * section.confidence)

        # If score is ambiguous, use LLMUtility for fallback semantic match
        if 0.2 < boosted_score < 0.5:
            try:
                llm_result = self.llm_utility.match_sections_with_llm(template['title'], section.title)
                if llm_result and llm_result.get('match', False):
                    boosted_score = max(boosted_score, 0.6)
            except Exception as e:
                logger.warning(f"LLM fallback match failed: {e}")

        return min(boosted_score, 1.0)
    
    def _generate_draft_sections(self, matched_sections: Dict[str, List[ContentSection]]) -> List[DraftSection]:
        """Generate draft sections from matched content."""
        draft_sections = []
        
        for template_id, sections in matched_sections.items():
            if not sections:
                continue
            
            template = next(t for t in self.template_sections if t['id'] == template_id)
            
            # Generate content for this template
            content = self._generate_section_content(sections, template)
            
            # Calculate confidence
            confidence = sum(s.confidence for s in sections) / len(sections)
            
            # Compile provenance
            provenance = self._compile_section_provenance(sections, template)
            
            draft_section = DraftSection(
                template_id=template_id,
                template_title=template['title'],
                content=content,
                confidence=confidence,
                source_sections=[s.id for s in sections],
                provenance=provenance,
                generated_at=datetime.now().isoformat()
            )
            
            draft_sections.append(draft_section)
        
        return draft_sections
    
    def _generate_section_content(self, sections: List[ContentSection], 
                                 template: Dict[str, Any]) -> str:
        """Generate content for a draft section."""
        if not sections:
            return f"# {template['title']}\n\n*Content not available in source documents.*"
        
        # For MVP, combine content with basic formatting
        content_parts = [f"# {template['title']}\n"]
        
        for i, section in enumerate(sections, 1):
            content_parts.append(f"## {section.title}\n")
            content_parts.append(f"{section.content}\n")
            
            if section.acronyms_found:
                content_parts.append("**Key Terms:** " + 
                                   ", ".join(f"{acronym} ({definition})" 
                                           for acronym, definition in section.acronyms_found[:3]))
                content_parts.append("\n")
        
        return "\n".join(content_parts)
    
    def _analyze_gaps(self, draft_sections: List[DraftSection]) -> List[GapAnalysis]:
        """Analyze gaps in documentation coverage."""
        gaps = []
        covered_templates = {section.template_id for section in draft_sections}
        
        for template in self.template_sections:
            if template['id'] not in covered_templates:
                severity = 'high' if template['required'] else 'medium'
                priority = 1 if template['required'] else 2
                
                gap = GapAnalysis(
                    template_section=template['title'],
                    severity=severity,
                    description=f"Missing content for {template['title']}",
                    suggested_content=f"Content needed for {template['title']} section",
                    priority=priority,
                    source="draft_generator"
                )
                gaps.append(gap)
        
        return gaps
    
    def _calculate_coverage(self, draft_sections: List[DraftSection]) -> float:
        """Calculate coverage percentage."""
        total_templates = len(self.template_sections)
        covered_templates = len(draft_sections)
        return (covered_templates / total_templates) * 100 if total_templates > 0 else 0
    
    def _calculate_confidence(self, draft_sections: List[DraftSection]) -> float:
        """Calculate overall confidence score."""
        if not draft_sections:
            return 0.0
        return sum(section.confidence for section in draft_sections) / len(draft_sections)
    
    def _compile_section_provenance(self, sections: List[ContentSection], 
                                   template: Dict[str, Any]) -> Dict[str, Any]:
        """Compile provenance information for a section."""
        return {
            'template_id': template['id'],
            'template_title': template['title'],
            'source_sections': [
                {
                    'id': s.id,
                    'title': s.title,
                    'source': s.source,
                    'confidence': s.confidence,
                    'timestamp': s.timestamp
                }
                for s in sections
            ],
            'total_sources': len(sections),
            'average_confidence': sum(s.confidence for s in sections) / len(sections) if sections else 0
        }
    
    def _compile_provenance(self, content_sections: List[ContentSection], 
                           draft_sections: List[DraftSection]) -> Dict[str, Any]:
        """Compile overall provenance summary."""
        return {
            'generation_timestamp': datetime.now().isoformat(),
            'total_content_sections': len(content_sections),
            'total_draft_sections': len(draft_sections),
            'sources_used': list(set(s.source for s in content_sections)),
            'template_coverage': {
                section.template_id: {
                    'title': section.template_title,
                    'confidence': section.confidence,
                    'word_count': section.word_count
                }
                for section in draft_sections
            },
            'acronym_expansion_used': True,
            'llm_enhancement_used': True
        }
    
    def save_draft(self, draft_result: DraftResult, output_path: str):
        """Save draft result to file."""
        output_data = asdict(draft_result)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Draft saved to: {output_path}")
    
    def export_markdown(self, draft_result: DraftResult, output_path: str):
        """Export draft as Markdown."""
        markdown_content = []
        
        # Header
        markdown_content.append(f"# {draft_result.document_title}")
        markdown_content.append("")
        markdown_content.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        markdown_content.append(f"*Coverage: {draft_result.coverage_percentage:.1f}%*")
        markdown_content.append(f"*Confidence: {draft_result.confidence_score:.2f}*")
        markdown_content.append("")
        
        # Sections
        for section in draft_result.sections:
            markdown_content.append(section.content)
            markdown_content.append("")
        
        # Gaps section
        if draft_result.gaps:
            markdown_content.append("## Documentation Gaps")
            markdown_content.append("")
            
            for gap in draft_result.gaps:
                markdown_content.append(f"### {gap.template_section}")
                markdown_content.append(f"**Severity:** {gap.severity}")
                markdown_content.append(f"**Priority:** {gap.priority}")
                markdown_content.append(f"**Description:** {gap.description}")
                markdown_content.append("")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(markdown_content))
        
        logger.info(f"Markdown exported to: {output_path}")


def main():
    """Test the draft generator."""
    # Create test content sections
    test_sections = [
        ContentSection(
            id="section_1",
            title="Nexus Hardware Overview",
            content="The Cisco Nexus 9000 Series switches provide high-performance, low-latency switching for data center environments.",
            source="nexus_guide.pdf",
            confidence=0.9,
            acronyms_found=[("Nexus", "Cisco Nexus"), ("Nexus 9000", "Cisco Nexus 9000 Series")]
        ),
        ContentSection(
            id="section_2",
            title="Installation Requirements",
            content="Before installing the Nexus switch, ensure you have the required tools and safety equipment.",
            source="nexus_guide.pdf",
            confidence=0.8,
            acronyms_found=[]
        )
    ]
    
    # Initialize generator
    generator = DraftGenerator()
    
    # Generate draft
    result = generator.generate_draft(test_sections, "Cisco Nexus 9000 Installation Guide")
    
    # Save results
    generator.save_draft(result, "test_draft_result.json")
    generator.export_markdown(result, "test_draft.md")
    
    print(f"✅ Draft generation completed!")
    print(f"   Coverage: {result.coverage_percentage:.1f}%")
    print(f"   Confidence: {result.confidence_score:.2f}")
    print(f"   Sections: {len(result.sections)}")
    print(f"   Gaps: {len(result.gaps)}")


if __name__ == "__main__":
    main() 