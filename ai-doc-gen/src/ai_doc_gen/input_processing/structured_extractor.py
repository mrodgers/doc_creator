"""
Structured Data Extractor

Extracts structured information from parsed documents, specifically designed
for hardware documentation with focus on technical specifications, procedures,
and requirements.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types of content that can be extracted."""
    TECHNICAL_SPEC = "technical_specification"
    INSTALLATION_PROCEDURE = "installation_procedure"
    REQUIREMENT = "requirement"
    WARNING = "warning"
    NOTE = "note"
    DIAGRAM_REFERENCE = "diagram_reference"
    TABLE_REFERENCE = "table_reference"
    STEP_BY_STEP = "step_by_step"
    CONFIGURATION = "configuration"
    TROUBLESHOOTING = "troubleshooting"

class ExtractedContent(BaseModel):
    """Structured representation of extracted content."""
    content_type: ContentType
    title: str
    content: str
    confidence: float
    source_section: str
    metadata: Dict[str, Any] = {}
    tags: List[str] = []

class StructuredExtractor:
    """Extracts structured content from parsed documents."""
    
    def __init__(self):
        """Initialize the extractor with patterns and rules."""
        self._init_patterns()
        self._init_keywords()
    
    def _init_patterns(self):
        """Initialize regex patterns for content identification."""
        self.patterns = {
            ContentType.TECHNICAL_SPEC: [
                r'(?i)(specifications?|specs?|technical\s+details?)',
                r'(?i)(dimensions?|weight|power|voltage|current)',
                r'(?i)(interface|connector|port|slot)',
                r'(?i)(capacity|memory|storage|bandwidth)',
            ],
            ContentType.INSTALLATION_PROCEDURE: [
                r'(?i)(install|installation|setup|mount)',
                r'(?i)(connect|wire|cable|plug)',
                r'(?i)(configure|initialize|boot)',
            ],
            ContentType.REQUIREMENT: [
                r'(?i)(require|requirement|prerequisite)',
                r'(?i)(minimum|maximum|recommended)',
                r'(?i)(compatible|supported|certified)',
            ],
            ContentType.WARNING: [
                r'(?i)(warning|caution|danger|hazard)',
                r'(?i)(do\s+not|never|avoid)',
                r'(?i)(critical|important|essential)',
            ],
            ContentType.NOTE: [
                r'(?i)(note|notice|tip|hint)',
                r'(?i)(information|info|details?)',
            ],
            ContentType.DIAGRAM_REFERENCE: [
                r'(?i)(figure|fig\.|diagram|drawing)',
                r'(?i)(see\s+figure|refer\s+to\s+diagram)',
            ],
            ContentType.TABLE_REFERENCE: [
                r'(?i)(table|chart|specification\s+sheet)',
                r'(?i)(see\s+table|refer\s+to\s+table)',
            ],
            ContentType.STEP_BY_STEP: [
                r'(?i)(step\s+\d+|procedure|instructions?)',
                r'(?i)(first|second|third|next|finally)',
                r'(?i)(1\.|2\.|3\.|4\.|5\.)',  # Numbered steps
            ],
            ContentType.CONFIGURATION: [
                r'(?i)(configure|configuration|settings?)',
                r'(?i)(parameter|option|setting)',
                r'(?i)(enable|disable|set\s+to)',
            ],
            ContentType.TROUBLESHOOTING: [
                r'(?i)(troubleshoot|troubleshooting|problem)',
                r'(?i)(error|fault|issue|symptom)',
                r'(?i)(solution|fix|resolve|correct)',
            ]
        }
    
    def _init_keywords(self):
        """Initialize keyword mappings for content classification."""
        self.keywords = {
            ContentType.TECHNICAL_SPEC: {
                'hardware': ['dimensions', 'weight', 'material', 'color'],
                'electrical': ['voltage', 'current', 'power', 'frequency'],
                'performance': ['speed', 'capacity', 'throughput', 'latency'],
                'connectivity': ['ports', 'interfaces', 'connectors', 'cables'],
            },
            ContentType.INSTALLATION_PROCEDURE: {
                'physical': ['mount', 'attach', 'secure', 'position'],
                'electrical': ['connect', 'wire', 'power', 'ground'],
                'configuration': ['configure', 'initialize', 'calibrate'],
            },
            ContentType.REQUIREMENT: {
                'environmental': ['temperature', 'humidity', 'altitude'],
                'electrical': ['power', 'voltage', 'current'],
                'physical': ['space', 'clearance', 'access'],
            }
        }
    
    def extract_structured_content(self, parsed_document) -> List[ExtractedContent]:
        """Extract structured content from a parsed document."""
        extracted_content = []
        
        # Process each section
        for section in parsed_document.sections:
            section_content = self._extract_from_section(section, parsed_document)
            extracted_content.extend(section_content)
        
        # Process raw text for additional content
        raw_content = self._extract_from_raw_text(parsed_document.raw_text)
        extracted_content.extend(raw_content)
        
        # Remove duplicates and sort by confidence
        unique_content = self._deduplicate_content(extracted_content)
        unique_content.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_content
    
    def _extract_from_section(self, section: Dict[str, Any], 
                            parsed_document) -> List[ExtractedContent]:
        """Extract content from a specific section."""
        extracted = []
        heading = section.get('heading', '')
        content_lines = section.get('content', [])
        
        # Analyze heading for content type
        heading_content = self._classify_content(heading, heading)
        if heading_content:
            heading_content.source_section = heading
            extracted.append(heading_content)
        
        # Analyze content lines
        content_text = '\n'.join(content_lines)
        if content_text.strip():
            content_items = self._extract_content_items(content_text, heading)
            extracted.extend(content_items)
        
        return extracted
    
    def _extract_from_raw_text(self, raw_text: str) -> List[ExtractedContent]:
        """Extract content from raw text when section structure is unclear."""
        extracted = []
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in raw_text.split('\n\n') if p.strip()]
        
        for paragraph in paragraphs:
            if len(paragraph) > 50:  # Only process substantial paragraphs
                content_item = self._classify_content(paragraph, "Raw Text")
                if content_item:
                    extracted.append(content_item)
        
        return extracted
    
    def _classify_content(self, text: str, context: str) -> Optional[ExtractedContent]:
        """Classify and extract content from text."""
        if not text.strip():
            return None
        
        # Prioritize warning patterns
        for pattern in self.patterns[ContentType.WARNING]:
            if re.search(pattern, text, re.IGNORECASE):
                return ExtractedContent(
                    content_type=ContentType.WARNING,
                    title=self._extract_title(text),
                    content=text,
                    confidence=0.8,
                    source_section=context,
                    tags=self._extract_tags(text, ContentType.WARNING)
                )
        
        # Score each content type
        scores = {}
        for content_type, patterns in self.patterns.items():
            if content_type == ContentType.WARNING:
                continue  # Already handled
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                score += len(matches) * 0.1
            
            # Additional scoring based on keywords
            keyword_score = self._calculate_keyword_score(text, content_type)
            score += keyword_score
            
            scores[content_type] = score
        
        # Find the best match
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0.1:  # Minimum threshold
                return ExtractedContent(
                    content_type=best_type[0],
                    title=self._extract_title(text),
                    content=text,
                    confidence=min(best_type[1], 1.0),
                    source_section=context,
                    tags=self._extract_tags(text, best_type[0])
                )
        
        return None
    
    def _calculate_keyword_score(self, text: str, content_type: ContentType) -> float:
        """Calculate score based on keyword presence."""
        if content_type not in self.keywords:
            return 0.0
        
        score = 0.0
        text_lower = text.lower()
        
        for category, keywords in self.keywords[content_type].items():
            for keyword in keywords:
                if keyword in text_lower:
                    score += 0.05
        
        return score
    
    def _extract_title(self, text: str) -> str:
        """Extract a title from text."""
        lines = text.split('\n')
        first_line = lines[0].strip()
        
        # If first line is short and looks like a title
        if len(first_line) < 100 and first_line.endswith(('.', ':', ';')):
            return first_line
        
        # Otherwise, create a title from the first few words
        words = text.split()[:5]
        return ' '.join(words) + ('...' if len(text.split()) > 5 else '')
    
    def _extract_tags(self, text: str, content_type: ContentType) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        text_lower = text.lower()
        
        # Extract technical terms
        technical_terms = [
            'cisco', 'router', 'switch', 'firewall', 'server',
            'ethernet', 'fiber', 'copper', 'wireless', 'bluetooth',
            'usb', 'hdmi', 'vga', 'serial', 'parallel'
        ]
        
        for term in technical_terms:
            if term in text_lower:
                tags.append(term)
        
        # Extract full measurements (e.g., 100V, 1GB)
        measurement_patterns = [
            r'\b\d+(?:\.\d+)?\s*(mm|cm|m|inch|ft)\b',  # Length
            r'\b\d+(?:\.\d+)?\s*(kg|lb|g)\b',          # Weight
            r'\b\d+(?:\.\d+)?\s*(V|A|W|Hz)\b',         # Electrical
            r'\b\d+(?:\.\d+)?\s*(GB|MB|TB)\b',         # Storage
            r'\b\d+(?:\.\d+)?\s*V\b',                  # e.g., 100V
            r'\b\d+(?:\.\d+)?\s*GB\b',                 # e.g., 1GB
        ]
        
        for pattern in measurement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in re.finditer(pattern, text, re.IGNORECASE):
                tags.append(match.group(0).strip())
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_content_items(self, content_text: str, 
                             section_heading: str) -> List[ExtractedContent]:
        """Extract multiple content items from a larger text block."""
        items = []
        
        # Split by common separators
        separators = ['\n\n', '•', '·', '- ', '* ']
        for separator in separators:
            if separator in content_text:
                parts = content_text.split(separator)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 20:
                        content_item = self._classify_content(part, section_heading)
                        if content_item:
                            items.append(content_item)
                break
        
        # If no separators found, try to split by sentences
        if not items:
            sentences = re.split(r'[.!?]+', content_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 30:
                    content_item = self._classify_content(sentence, section_heading)
                    if content_item:
                        items.append(content_item)
        
        return items
    
    def _deduplicate_content(self, content_list: List[ExtractedContent]) -> List[ExtractedContent]:
        """Remove duplicate content items."""
        seen = set()
        unique_content = []
        
        for item in content_list:
            # Create a hash of the content for deduplication
            content_hash = hash(item.content.lower().strip())
            
            if content_hash not in seen:
                seen.add(content_hash)
                unique_content.append(item)
        
        return unique_content
    
    def get_content_summary(self, extracted_content: List[ExtractedContent]) -> Dict[str, Any]:
        """Generate a summary of extracted content."""
        summary = {
            'total_items': len(extracted_content),
            'content_types': {},
            'confidence_distribution': {
                'high': 0,    # 0.8-1.0
                'medium': 0,  # 0.5-0.79
                'low': 0      # 0.1-0.49
            },
            'top_tags': {},
            'sections_covered': set()
        }
        
        for item in extracted_content:
            # Count content types
            content_type = item.content_type.value
            summary['content_types'][content_type] = summary['content_types'].get(content_type, 0) + 1
            
            # Count confidence levels
            if item.confidence >= 0.8:
                summary['confidence_distribution']['high'] += 1
            elif item.confidence >= 0.5:
                summary['confidence_distribution']['medium'] += 1
            else:
                summary['confidence_distribution']['low'] += 1
            
            # Count tags
            for tag in item.tags:
                summary['top_tags'][tag] = summary['top_tags'].get(tag, 0) + 1
            
            # Track sections
            summary['sections_covered'].add(item.source_section)
        
        # Convert set to list for JSON serialization
        summary['sections_covered'] = list(summary['sections_covered'])
        
        # Sort tags by frequency
        summary['top_tags'] = dict(
            sorted(summary['top_tags'].items(), 
                  key=lambda x: x[1], reverse=True)[:10]
        )
        
        return summary

# Convenience function
def extract_structured_content(parsed_document) -> List[ExtractedContent]:
    """Extract structured content from a parsed document."""
    extractor = StructuredExtractor()
    return extractor.extract_structured_content(parsed_document) 