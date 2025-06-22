"""
Advanced NLP Entity Extractor

This module provides advanced NLP capabilities including entity recognition,
relationship extraction, and technical term identification for hardware documentation.
"""

import re
import spacy
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Please install with: python -m spacy download en_core_web_sm")
    nlp = None


@dataclass
class TechnicalEntity:
    """Represents a technical entity found in documentation."""
    text: str
    entity_type: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str
    attributes: Dict[str, Any]


@dataclass
class EntityRelationship:
    """Represents a relationship between technical entities."""
    entity1: TechnicalEntity
    entity2: TechnicalEntity
    relationship_type: str
    confidence: float
    context: str


class TechnicalEntityExtractor:
    """Advanced entity extractor for technical documentation."""
    
    def __init__(self):
        """Initialize the entity extractor."""
        self.nlp = nlp
        self.technical_patterns = self._load_technical_patterns()
        self.hardware_entities = self._load_hardware_entities()
        self.specification_patterns = self._load_specification_patterns()
        
    def _load_technical_patterns(self) -> Dict[str, List[str]]:
        """Load technical pattern definitions."""
        return {
            'hardware_components': [
                r'\b(switch|router|server|chassis|module|card|port|interface|connector)\b',
                r'\b(CPU|GPU|RAM|ROM|SSD|HDD|NIC|PSU|fan|cooling)\b',
                r'\b(Cisco|Nexus|Catalyst|ASR|ISR|Meraki)\b',
                r'\b(ethernet|fiber|copper|wireless|bluetooth|usb|serial|parallel)\b'
            ],
            'specifications': [
                r'\b(\d+(?:\.\d+)?)\s*(Gbps|Mbps|Kbps|Hz|MHz|GHz|TB|GB|MB|KB|W|V|A|mA)\b',
                r'\b(\d+(?:\.\d+)?)\s*(port|slot|module|card|interface|connector)s?\b',
                r'\b(\d+(?:\.\d+)?)\s*(degree|°C|°F|percent|%)\b',
                r'\b(minimum|maximum|recommended|required)\s+(\d+(?:\.\d+)?)\b'
            ],
            'procedures': [
                r'\b(install|configure|setup|deploy|connect|power|boot|shutdown)\b',
                r'\b(mount|rack|cable|wire|plug|unplug|insert|remove)\b',
                r'\b(verify|test|check|validate|confirm|ensure)\b',
                r'\b(troubleshoot|diagnose|repair|maintain|service|upgrade)\b'
            ],
            'safety_terms': [
                r'\b(warning|caution|danger|hazard|risk|precaution)\b',
                r'\b(voltage|current|power|electrical|shock|fire)\b',
                r'\b(ground|earth|bonding|isolation|protection)\b',
                r'\b(ESD|electrostatic|discharge|static)\b'
            ]
        }
    
    def _load_hardware_entities(self) -> Dict[str, List[str]]:
        """Load hardware entity definitions."""
        return {
            'cisco_switches': [
                'Nexus 9000', 'Nexus 7000', 'Nexus 5000', 'Nexus 3000',
                'Catalyst 9000', 'Catalyst 8000', 'Catalyst 6000', 'Catalyst 5000',
                'Catalyst 4000', 'Catalyst 3000', 'Catalyst 2000'
            ],
            'cisco_routers': [
                'ASR 9000', 'ASR 1000', 'ASR 900', 'ASR 100',
                'ISR 4000', 'ISR 1000', 'ISR 900', 'ISR 800'
            ],
            'hardware_components': [
                'Supervisor Engine', 'Line Card', 'Power Supply', 'Fan Module',
                'Interface Module', 'Transceiver', 'Cable', 'Connector',
                'Chassis', 'Backplane', 'Motherboard', 'Processor'
            ],
            'specifications': [
                'Port Count', 'Bandwidth', 'Power Consumption', 'Temperature',
                'Dimensions', 'Weight', 'Voltage', 'Current', 'Frequency',
                'Memory', 'Storage', 'Processing Power'
            ]
        }
    
    def _load_specification_patterns(self) -> List[str]:
        """Load specification pattern definitions."""
        return [
            r'(\d+(?:\.\d+)?)\s*(Gbps|Mbps|Kbps)',
            r'(\d+(?:\.\d+)?)\s*(W|watts)',
            r'(\d+(?:\.\d+)?)\s*(V|volts)',
            r'(\d+(?:\.\d+)?)\s*(A|amps)',
            r'(\d+(?:\.\d+)?)\s*(°C|°F|degrees)',
            r'(\d+(?:\.\d+)?)\s*(GB|MB|KB|TB)',
            r'(\d+(?:\.\d+)?)\s*(MHz|GHz|Hz)',
            r'(\d+(?:\.\d+)?)\s*(port|slot|module)s?',
            r'(\d+(?:\.\d+)?)\s*(inch|mm|cm)',
            r'(\d+(?:\.\d+)?)\s*(lb|kg|pound)s?'
        ]
    
    def extract_entities(self, text: str) -> List[TechnicalEntity]:
        """Extract technical entities from text."""
        entities = []
        
        if not self.nlp:
            logger.warning("spaCy not available, using pattern-based extraction only")
            return self._extract_entities_pattern_based(text)
        
        # Use spaCy for NLP-based extraction
        doc = self.nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'QUANTITY', 'CARDINAL']:
                entity = TechnicalEntity(
                    text=ent.text,
                    entity_type=ent.label_,
                    confidence=0.8,
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    context=ent.sent.text,
                    attributes={'spacy_label': ent.label_}
                )
                entities.append(entity)
        
        # Extract technical patterns
        pattern_entities = self._extract_entities_pattern_based(text)
        entities.extend(pattern_entities)
        
        # Extract hardware-specific entities
        hardware_entities = self._extract_hardware_entities(text)
        entities.extend(hardware_entities)
        
        # Extract specifications
        spec_entities = self._extract_specifications(text)
        entities.extend(spec_entities)
        
        return entities
    
    def _extract_entities_pattern_based(self, text: str) -> List[TechnicalEntity]:
        """Extract entities using pattern matching."""
        entities = []
        
        for entity_type, patterns in self.technical_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = TechnicalEntity(
                        text=match.group(),
                        entity_type=entity_type,
                        confidence=0.7,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=self._get_context(text, match.start(), match.end()),
                        attributes={'pattern': pattern}
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_hardware_entities(self, text: str) -> List[TechnicalEntity]:
        """Extract hardware-specific entities."""
        entities = []
        
        for category, items in self.hardware_entities.items():
            for item in items:
                matches = re.finditer(rf'\b{re.escape(item)}\b', text, re.IGNORECASE)
                for match in matches:
                    entity = TechnicalEntity(
                        text=match.group(),
                        entity_type=f'hardware_{category}',
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=self._get_context(text, match.start(), match.end()),
                        attributes={'category': category, 'hardware_type': item}
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_specifications(self, text: str) -> List[TechnicalEntity]:
        """Extract specification entities."""
        entities = []
        
        for pattern in self.specification_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                unit = match.group(2) if len(match.groups()) > 1 else ''
                
                entity = TechnicalEntity(
                    text=match.group(),
                    entity_type='specification',
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=self._get_context(text, match.start(), match.end()),
                    attributes={
                        'value': value,
                        'unit': unit,
                        'pattern': pattern
                    }
                )
                entities.append(entity)
        
        return entities
    
    def _get_context(self, text: str, start: int, end: int, context_size: int = 100) -> str:
        """Get context around a match."""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()
    
    def extract_relationships(self, entities: List[TechnicalEntity]) -> List[EntityRelationship]:
        """Extract relationships between entities."""
        relationships = []
        
        # Find entities that are close to each other
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                # Check if entities are close in the text
                distance = abs(entity1.start_pos - entity2.start_pos)
                if distance < 200:  # Within 200 characters
                    relationship = self._determine_relationship(entity1, entity2)
                    if relationship:
                        relationships.append(relationship)
        
        return relationships
    
    def _determine_relationship(self, entity1: TechnicalEntity, entity2: TechnicalEntity) -> Optional[EntityRelationship]:
        """Determine the relationship between two entities."""
        # Hardware component relationships
        if entity1.entity_type == 'hardware_components' and entity2.entity_type == 'specification':
            return EntityRelationship(
                entity1=entity1,
                entity2=entity2,
                relationship_type='has_specification',
                confidence=0.8,
                context=f"{entity1.text} has specification {entity2.text}"
            )
        
        # Safety relationships
        if entity1.entity_type == 'safety_terms' and entity2.entity_type in ['hardware_components', 'specification']:
            return EntityRelationship(
                entity1=entity1,
                entity2=entity2,
                relationship_type='safety_related',
                confidence=0.7,
                context=f"Safety {entity1.text} related to {entity2.text}"
            )
        
        # Procedure relationships
        if entity1.entity_type == 'procedures' and entity2.entity_type == 'hardware_components':
            return EntityRelationship(
                entity1=entity1,
                entity2=entity2,
                relationship_type='applies_to',
                confidence=0.8,
                context=f"Procedure {entity1.text} applies to {entity2.text}"
            )
        
        return None
    
    def get_entity_summary(self, entities: List[TechnicalEntity]) -> Dict[str, Any]:
        """Get a summary of extracted entities."""
        if not entities:
            return {}
        
        # Count by type
        type_counts = {}
        for entity in entities:
            type_counts[entity.entity_type] = type_counts.get(entity.entity_type, 0) + 1
        
        # Get unique entities
        unique_entities = {}
        for entity in entities:
            key = f"{entity.entity_type}:{entity.text.lower()}"
            if key not in unique_entities:
                unique_entities[key] = entity
        
        # Calculate confidence statistics
        confidences = [entity.confidence for entity in entities]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'total_entities': len(entities),
            'unique_entities': len(unique_entities),
            'type_distribution': type_counts,
            'average_confidence': avg_confidence,
            'high_confidence_entities': [e for e in entities if e.confidence > 0.8],
            'entity_types_found': list(type_counts.keys())
        }


class DocumentEntityAnalyzer:
    """Analyzes entities across entire documents."""
    
    def __init__(self):
        """Initialize the document analyzer."""
        self.extractor = TechnicalEntityExtractor()
    
    def analyze_document(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze entities across document sections."""
        all_entities = []
        all_relationships = []
        section_analyses = []
        
        for section in sections:
            heading = section.get('heading', '')
            content = section.get('content', [])
            
            # Combine heading and content
            text = heading + " " + " ".join(content)
            
            # Extract entities
            entities = self.extractor.extract_entities(text)
            relationships = self.extractor.extract_relationships(entities)
            
            # Store results
            all_entities.extend(entities)
            all_relationships.extend(relationships)
            
            section_analysis = {
                'section_heading': heading,
                'entities_found': len(entities),
                'relationships_found': len(relationships),
                'entity_types': list(set(e.entity_type for e in entities)),
                'high_confidence_entities': [e for e in entities if e.confidence > 0.8]
            }
            section_analyses.append(section_analysis)
        
        # Overall analysis
        overall_summary = self.extractor.get_entity_summary(all_entities)
        
        return {
            'document_summary': overall_summary,
            'section_analyses': section_analyses,
            'all_entities': [
                {
                    'text': e.text,
                    'type': e.entity_type,
                    'confidence': e.confidence,
                    'context': e.context
                }
                for e in all_entities
            ],
            'relationships': [
                {
                    'entity1': r.entity1.text,
                    'entity2': r.entity2.text,
                    'relationship': r.relationship_type,
                    'confidence': r.confidence,
                    'context': r.context
                }
                for r in all_relationships
            ]
        } 