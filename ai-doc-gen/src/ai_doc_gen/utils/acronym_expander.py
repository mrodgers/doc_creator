#!/usr/bin/env python3
"""
Acronym Expansion Module for Cisco Documentation
Integrates Cisco acronyms to improve section matching and synonym generation.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AcronymExpander:
    """Expands acronyms in section titles and provides bidirectional mapping."""
    
    def __init__(self, acronyms_file: str = "cisco_acronyms_comprehensive.json"):
        self.acronyms_file = acronyms_file
        self.acronyms_dict = {}
        self.reverse_mapping = {}  # full term -> acronyms
        self.load_acronyms()
    
    def load_acronyms(self):
        """Load acronyms from JSON file."""
        try:
            if os.path.exists(self.acronyms_file):
                with open(self.acronyms_file, 'r') as f:
                    self.acronyms_dict = json.load(f)
                logger.info(f"Loaded {len(self.acronyms_dict)} acronyms from {self.acronyms_file}")
            else:
                logger.warning(f"Acronyms file not found: {self.acronyms_file}")
                self._load_default_acronyms()
            
            # Build reverse mapping
            self._build_reverse_mapping()
            
        except Exception as e:
            logger.error(f"Failed to load acronyms: {e}")
            self._load_default_acronyms()
            self._build_reverse_mapping()
    
    def _load_default_acronyms(self):
        """Load default Cisco acronyms if file not available."""
        default_acronyms = {
            'PoE': 'Power over Ethernet',
            'VLAN': 'Virtual Local Area Network',
            'ACL': 'Access Control List',
            'SNMP': 'Simple Network Management Protocol',
            'SSH': 'Secure Shell',
            'TFTP': 'Trivial File Transfer Protocol',
            'FTP': 'File Transfer Protocol',
            'HTTP': 'Hypertext Transfer Protocol',
            'HTTPS': 'Hypertext Transfer Protocol Secure',
            'DNS': 'Domain Name System',
            'DHCP': 'Dynamic Host Configuration Protocol',
            'NTP': 'Network Time Protocol',
            'BGP': 'Border Gateway Protocol',
            'OSPF': 'Open Shortest Path First',
            'EIGRP': 'Enhanced Interior Gateway Routing Protocol',
            'RIP': 'Routing Information Protocol',
            'STP': 'Spanning Tree Protocol',
            'RSTP': 'Rapid Spanning Tree Protocol',
            'MSTP': 'Multiple Spanning Tree Protocol',
            'VRRP': 'Virtual Router Redundancy Protocol',
            'HSRP': 'Hot Standby Router Protocol',
            'GLBP': 'Gateway Load Balancing Protocol',
            'QoS': 'Quality of Service',
            'CoS': 'Class of Service',
            'ToS': 'Type of Service',
            'DSCP': 'Differentiated Services Code Point',
            'MPLS': 'Multiprotocol Label Switching',
            'VPN': 'Virtual Private Network',
            'IPSec': 'Internet Protocol Security',
            'GRE': 'Generic Routing Encapsulation',
            'L2TP': 'Layer 2 Tunneling Protocol',
            'PPTP': 'Point-to-Point Tunneling Protocol',
            'RADIUS': 'Remote Authentication Dial-In User Service',
            'TACACS+': 'Terminal Access Controller Access-Control System Plus',
            'AAA': 'Authentication, Authorization, and Accounting',
            'NAC': 'Network Access Control',
            '802.1X': 'IEEE 802.1X Port-Based Network Access Control',
            'CDP': 'Cisco Discovery Protocol',
            'LLDP': 'Link Layer Discovery Protocol',
            'LACP': 'Link Aggregation Control Protocol',
            'PAgP': 'Port Aggregation Protocol',
            'EtherChannel': 'Ethernet Channel',
            'PortChannel': 'Port Channel',
            'VPC': 'Virtual Port Channel',
            'FCoE': 'Fibre Channel over Ethernet',
            'iSCSI': 'Internet Small Computer System Interface',
            'FC': 'Fibre Channel',
            'SAN': 'Storage Area Network',
            'NAS': 'Network Attached Storage',
            'RAID': 'Redundant Array of Independent Disks',
            'NVRAM': 'Non-Volatile Random Access Memory',
            'ROM': 'Read-Only Memory',
            'RAM': 'Random Access Memory',
            'CPU': 'Central Processing Unit',
            'ASIC': 'Application-Specific Integrated Circuit',
            'FPGA': 'Field-Programmable Gate Array',
            'UCS': 'Unified Computing System',
            'ACI': 'Application Centric Infrastructure',
            'SDN': 'Software-Defined Networking',
            'NFV': 'Network Functions Virtualization',
            'VXLAN': 'Virtual Extensible Local Area Network',
            'NVGRE': 'Network Virtualization using Generic Routing Encapsulation',
            'GENEVE': 'Generic Network Virtualization Encapsulation',
            'OTV': 'Overlay Transport Virtualization',
            'LISP': 'Locator/ID Separation Protocol',
            'PIM': 'Protocol Independent Multicast',
            'IGMP': 'Internet Group Management Protocol',
            'PIM-SM': 'Protocol Independent Multicast - Sparse Mode',
            'PIM-DM': 'Protocol Independent Multicast - Dense Mode',
            'MSDP': 'Multicast Source Discovery Protocol',
            'MBGP': 'Multiprotocol Border Gateway Protocol',
            'RP': 'Rendezvous Point',
            'BSR': 'Bootstrap Router',
            'Auto-RP': 'Automatic Rendezvous Point',
            'Anycast-RP': 'Anycast Rendezvous Point',
            'SSM': 'Source-Specific Multicast',
            'ASM': 'Any-Source Multicast',
            'IGMPv1': 'Internet Group Management Protocol version 1',
            'IGMPv2': 'Internet Group Management Protocol version 2',
            'IGMPv3': 'Internet Group Management Protocol version 3',
            'MLD': 'Multicast Listener Discovery',
            'MLDv1': 'Multicast Listener Discovery version 1',
            'MLDv2': 'Multicast Listener Discovery version 2'
        }
        
        for acronym, definition in default_acronyms.items():
            self.acronyms_dict[acronym] = {
                'definition': definition,
                'source': 'default',
                'category': 'networking'
            }
        
        logger.info(f"Loaded {len(self.acronyms_dict)} default acronyms")
    
    def _build_reverse_mapping(self):
        """Build reverse mapping from full terms to acronyms."""
        self.reverse_mapping = {}
        for acronym, data in self.acronyms_dict.items():
            full_term = data['definition']
            if full_term not in self.reverse_mapping:
                self.reverse_mapping[full_term] = []
            self.reverse_mapping[full_term].append(acronym)
    
    def expand_acronyms_in_text(self, text: str) -> str:
        """Expand acronyms in text to their full definitions."""
        expanded_text = text
        for acronym, data in self.acronyms_dict.items():
            # Replace acronym with full definition
            expanded_text = expanded_text.replace(acronym, f"{acronym} ({data['definition']})")
        return expanded_text
    
    def find_acronyms_in_text(self, text: str) -> List[Tuple[str, str]]:
        """Find acronyms in text and return (acronym, definition) pairs."""
        found_acronyms = []
        text_upper = text.upper()
        
        for acronym, data in self.acronyms_dict.items():
            if acronym in text_upper:
                found_acronyms.append((acronym, data['definition']))
        
        return found_acronyms
    
    def get_acronym_synonyms(self, text: str) -> List[str]:
        """Get acronym synonyms for a given text."""
        synonyms = []
        
        # Find acronyms in the text
        found_acronyms = self.find_acronyms_in_text(text)
        for acronym, definition in found_acronyms:
            synonyms.append(acronym)
            synonyms.append(definition)
        
        # Find full terms that match the text
        text_lower = text.lower()
        for full_term, acronyms in self.reverse_mapping.items():
            if full_term.lower() in text_lower:
                synonyms.extend(acronyms)
        
        return list(set(synonyms))  # Remove duplicates
    
    def enhance_section_title(self, title: str) -> Dict[str, any]:
        """Enhance a section title with acronym information."""
        enhanced = {
            'original': title,
            'expanded': title,
            'acronyms_found': [],
            'synonyms': [],
            'enhanced_synonyms': []
        }
        
        # Find acronyms in the title
        found_acronyms = self.find_acronyms_in_text(title)
        enhanced['acronyms_found'] = found_acronyms
        
        # Expand the title
        enhanced['expanded'] = self.expand_acronyms_in_text(title)
        
        # Get acronym synonyms
        enhanced['synonyms'] = self.get_acronym_synonyms(title)
        
        # Create enhanced synonyms list
        enhanced['enhanced_synonyms'] = enhanced['synonyms'].copy()
        
        # Add expanded versions
        for acronym, definition in found_acronyms:
            enhanced['enhanced_synonyms'].append(f"{acronym} ({definition})")
            enhanced['enhanced_synonyms'].append(f"{definition} ({acronym})")
        
        return enhanced
    
    def get_acronym_statistics(self) -> Dict[str, any]:
        """Get statistics about loaded acronyms."""
        categories = {}
        for acronym, data in self.acronyms_dict.items():
            category = data.get('category', 'unknown')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            'total_acronyms': len(self.acronyms_dict),
            'categories': categories,
            'sources': list(set(data.get('source', 'unknown') for data in self.acronyms_dict.values()))
        }


def create_enhanced_synonym_prompt(title: str, acronym_expander: AcronymExpander) -> str:
    """Create an enhanced synonym prompt that includes acronym information."""
    enhanced = acronym_expander.enhance_section_title(title)
    
    prompt = f'For the documentation section title "{title}", list all common synonyms and abbreviations '
    prompt += 'used in Cisco hardware documentation. Focus on technical terms, acronyms, and variations '
    prompt += 'that would appear in official documentation. '
    
    if enhanced['acronyms_found']:
        prompt += f'\n\nNote: This title contains the following acronyms: '
        for acronym, definition in enhanced['acronyms_found']:
            prompt += f'{acronym} ({definition}), '
        prompt = prompt.rstrip(', ') + '. '
        prompt += 'Include both the acronym and full term variations in your response.'
    
    prompt += '\n\nReturn as a Python list of strings only.'
    
    return prompt


if __name__ == "__main__":
    # Test the acronym expander
    expander = AcronymExpander()
    
    # Test cases
    test_titles = [
        "PoE Configuration",
        "VLAN Setup",
        "Network Configuration",
        "Power over Ethernet Setup",
        "Quality of Service Configuration"
    ]
    
    print("🔤 Acronym Expander Test")
    print("=" * 40)
    
    for title in test_titles:
        enhanced = expander.enhance_section_title(title)
        print(f"\n📋 Title: {title}")
        print(f"   Expanded: {enhanced['expanded']}")
        print(f"   Acronyms: {enhanced['acronyms_found']}")
        print(f"   Synonyms: {enhanced['synonyms'][:5]}...")
    
    # Show statistics
    stats = expander.get_acronym_statistics()
    print(f"\n📊 Acronym Statistics:")
    print(f"   Total acronyms: {stats['total_acronyms']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   Sources: {stats['sources']}") 