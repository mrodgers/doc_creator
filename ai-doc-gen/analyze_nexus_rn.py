#!/usr/bin/env python3
"""
Analyze Nexus Release Notes PDF for Nexus-specific definitions and acronyms.
"""

import json
import re
import os
import sys
from pathlib import Path
import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text


def analyze_nexus_content(text: str) -> dict:
    """Analyze the Nexus release notes content for patterns."""
    lines = text.split('\n')
    
    # Find page boundaries
    page_markers = []
    for i, line in enumerate(lines):
        if line.startswith('=== PAGE'):
            page_markers.append(i)
    
    # Analyze content patterns
    nexus_terms = []
    acronyms = []
    features = []
    specifications = []
    current_page = 1
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for page boundaries
        if line.startswith('=== PAGE'):
            current_page = int(line.split()[2])
            continue
            
        # Look for Nexus-specific terms and features
        nexus_patterns = [
            r'Nexus\s+\d+',  # Nexus model numbers
            r'NX-OS',        # NX-OS operating system
            r'ACI\s+Mode',   # ACI mode
            r'Standalone\s+Mode',  # Standalone mode
            r'Fabric\s+Extender',  # Fabric Extender
            r'FEX',          # FEX abbreviation
            r'VPC',          # Virtual Port Channel
            r'vPC',          # Virtual Port Channel
            r'EtherChannel', # EtherChannel
            r'Port\s+Channel', # Port Channel
            r'VLAN',         # VLAN
            r'VRF',          # Virtual Routing and Forwarding
            r'BGP',          # Border Gateway Protocol
            r'OSPF',         # Open Shortest Path First
            r'EIGRP',        # Enhanced Interior Gateway Routing Protocol
            r'STP',          # Spanning Tree Protocol
            r'RSTP',         # Rapid Spanning Tree Protocol
            r'MSTP',         # Multiple Spanning Tree Protocol
            r'QoS',          # Quality of Service
            r'CoS',          # Class of Service
            r'DSCP',         # Differentiated Services Code Point
            r'ACL',          # Access Control List
            r'SNMP',         # Simple Network Management Protocol
            r'Syslog',       # System logging
            r'SSH',          # Secure Shell
            r'Telnet',       # Telnet
            r'TFTP',         # Trivial File Transfer Protocol
            r'FTP',          # File Transfer Protocol
            r'HTTP',         # Hypertext Transfer Protocol
            r'HTTPS',        # Hypertext Transfer Protocol Secure
            r'DNS',          # Domain Name System
            r'DHCP',         # Dynamic Host Configuration Protocol
            r'NTP',          # Network Time Protocol
            r'PIM',          # Protocol Independent Multicast
            r'IGMP',         # Internet Group Management Protocol
            r'HSRP',         # Hot Standby Router Protocol
            r'VRRP',         # Virtual Router Redundancy Protocol
            r'GLBP',         # Gateway Load Balancing Protocol
            r'CDP',          # Cisco Discovery Protocol
            r'LLDP',         # Link Layer Discovery Protocol
            r'LACP',         # Link Aggregation Control Protocol
            r'PAgP',         # Port Aggregation Protocol
            r'UDLD',         # Unidirectional Link Detection
            r'L2TP',         # Layer 2 Tunneling Protocol
            r'GRE',          # Generic Routing Encapsulation
            r'IPSec',        # Internet Protocol Security
            r'MPLS',         # Multiprotocol Label Switching
            r'VXLAN',        # Virtual Extensible Local Area Network
            r'NVGRE',        # Network Virtualization using Generic Routing Encapsulation
            r'GENEVE',       # Generic Network Virtualization Encapsulation
            r'OTV',          # Overlay Transport Virtualization
            r'LISP',         # Locator/ID Separation Protocol
            r'FCoE',         # Fibre Channel over Ethernet
            r'iSCSI',        # Internet Small Computer System Interface
            r'FC',           # Fibre Channel
            r'SAN',          # Storage Area Network
            r'NAS',          # Network Attached Storage
            r'RAID',         # Redundant Array of Independent Disks
            r'NVRAM',        # Non-Volatile Random Access Memory
            r'ROM',          # Read-Only Memory
            r'RAM',          # Random Access Memory
            r'CPU',          # Central Processing Unit
            r'ASIC',         # Application-Specific Integrated Circuit
            r'FPGA',         # Field-Programmable Gate Array
            r'UCS',          # Unified Computing System
            r'SDN',          # Software-Defined Networking
            r'NFV',          # Network Functions Virtualization
        ]
        
        for pattern in nexus_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                nexus_terms.append({
                    'term': match,
                    'line': i,
                    'page': current_page,
                    'context': line[:100] + '...' if len(line) > 100 else line
                })
        
        # Look for feature descriptions
        if any(keyword in line.lower() for keyword in ['feature', 'functionality', 'capability', 'support']):
            features.append({
                'line': i,
                'page': current_page,
                'text': line
            })
        
        # Look for specifications
        if any(keyword in line.lower() for keyword in ['specification', 'spec', 'requirement', 'parameter']):
            specifications.append({
                'line': i,
                'page': current_page,
                'text': line
            })
    
    return {
        'total_lines': len(lines),
        'pages': len(page_markers),
        'nexus_terms': nexus_terms,
        'features': features,
        'specifications': specifications,
        'sample_content': lines[100:120]  # Sample content for analysis
    }


def extract_nexus_acronyms(text: str) -> dict:
    """Extract Nexus-specific acronyms and definitions."""
    lines = text.split('\n')
    
    # Nexus-specific acronyms and their definitions
    nexus_acronyms = {
        # Nexus-specific terms
        'NX-OS': 'Cisco NX-OS Operating System',
        'ACI': 'Application Centric Infrastructure',
        'FEX': 'Fabric Extender',
        'VPC': 'Virtual Port Channel',
        'vPC': 'Virtual Port Channel',
        'VRF': 'Virtual Routing and Forwarding',
        'UDLD': 'Unidirectional Link Detection',
        
        # Hardware and components
        'ASIC': 'Application-Specific Integrated Circuit',
        'FPGA': 'Field-Programmable Gate Array',
        'NVRAM': 'Non-Volatile Random Access Memory',
        'ROM': 'Read-Only Memory',
        'RAM': 'Random Access Memory',
        'CPU': 'Central Processing Unit',
        
        # Networking protocols
        'BGP': 'Border Gateway Protocol',
        'OSPF': 'Open Shortest Path First',
        'EIGRP': 'Enhanced Interior Gateway Routing Protocol',
        'STP': 'Spanning Tree Protocol',
        'RSTP': 'Rapid Spanning Tree Protocol',
        'MSTP': 'Multiple Spanning Tree Protocol',
        'QoS': 'Quality of Service',
        'CoS': 'Class of Service',
        'DSCP': 'Differentiated Services Code Point',
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
        'PIM': 'Protocol Independent Multicast',
        'IGMP': 'Internet Group Management Protocol',
        'HSRP': 'Hot Standby Router Protocol',
        'VRRP': 'Virtual Router Redundancy Protocol',
        'GLBP': 'Gateway Load Balancing Protocol',
        'CDP': 'Cisco Discovery Protocol',
        'LLDP': 'Link Layer Discovery Protocol',
        'LACP': 'Link Aggregation Control Protocol',
        'PAgP': 'Port Aggregation Protocol',
        'L2TP': 'Layer 2 Tunneling Protocol',
        'GRE': 'Generic Routing Encapsulation',
        'IPSec': 'Internet Protocol Security',
        'MPLS': 'Multiprotocol Label Switching',
        'VXLAN': 'Virtual Extensible Local Area Network',
        'NVGRE': 'Network Virtualization using Generic Routing Encapsulation',
        'GENEVE': 'Generic Network Virtualization Encapsulation',
        'OTV': 'Overlay Transport Virtualization',
        'LISP': 'Locator/ID Separation Protocol',
        'FCoE': 'Fibre Channel over Ethernet',
        'iSCSI': 'Internet Small Computer System Interface',
        'FC': 'Fibre Channel',
        'SAN': 'Storage Area Network',
        'NAS': 'Network Attached Storage',
        'RAID': 'Redundant Array of Independent Disks',
        'UCS': 'Unified Computing System',
        'SDN': 'Software-Defined Networking',
        'NFV': 'Network Functions Virtualization',
        
        # Common networking terms
        'VLAN': 'Virtual Local Area Network',
        'EtherChannel': 'Ethernet Channel',
        'PortChannel': 'Port Channel',
        'Syslog': 'System Logging',
        'Telnet': 'Telecommunications Network',
    }
    
    # Add extracted acronyms to the dictionary
    nexus_acronyms_enhanced = {}
    for acronym, definition in nexus_acronyms.items():
        nexus_acronyms_enhanced[acronym] = {
            'definition': definition,
            'source': 'nexus_release_notes',
            'category': 'nexus_networking'
        }
    
    return nexus_acronyms_enhanced


def extract_nexus_features(text: str) -> list:
    """Extract Nexus-specific features and capabilities."""
    lines = text.split('\n')
    features = []
    
    # Look for feature descriptions in the text
    feature_keywords = [
        'feature', 'functionality', 'capability', 'support', 'enabled', 'disabled',
        'configuration', 'management', 'monitoring', 'security', 'performance',
        'scalability', 'reliability', 'availability', 'redundancy', 'backup',
        'restore', 'upgrade', 'downgrade', 'migration', 'conversion'
    ]
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in feature_keywords):
            # Check if line contains meaningful content
            if len(line.strip()) > 20 and not line.strip().startswith('==='):
                features.append({
                    'line_number': i,
                    'text': line.strip(),
                    'keywords': [kw for kw in feature_keywords if kw in line_lower]
                })
    
    return features


def main():
    """Main analysis function."""
    pdf_path = "nexus_rn.pdf"
    
    print("🔍 Analyzing Nexus Release Notes PDF...")
    print("=" * 60)
    
    # Extract text from PDF
    print("📄 Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("❌ Failed to extract text from PDF")
        return
    
    print(f"✅ Extracted {len(text)} characters of text")
    
    # Analyze content structure
    print("\n📊 Analyzing content structure...")
    analysis = analyze_nexus_content(text)
    
    print(f"📈 Content Analysis:")
    print(f"   Total lines: {analysis['total_lines']}")
    print(f"   Pages: {analysis['pages']}")
    print(f"   Nexus terms found: {len(analysis['nexus_terms'])}")
    print(f"   Features found: {len(analysis['features'])}")
    print(f"   Specifications found: {len(analysis['specifications'])}")
    
    # Show sample content
    print(f"\n📋 Sample Content (lines 100-120):")
    for line in analysis['sample_content']:
        if line.strip():
            print(f"   {line}")
    
    # Show Nexus terms
    if analysis['nexus_terms']:
        print(f"\n🔤 Nexus Terms Found:")
        unique_terms = set(term['term'] for term in analysis['nexus_terms'])
        for term in sorted(list(unique_terms))[:20]:
            print(f"   - {term}")
    
    # Extract Nexus acronyms
    print(f"\n📚 Extracting Nexus acronyms...")
    nexus_acronyms = extract_nexus_acronyms(text)
    
    print(f"✅ Extracted {len(nexus_acronyms)} Nexus acronyms")
    
    # Extract features
    print(f"\n🔧 Extracting Nexus features...")
    features = extract_nexus_features(text)
    
    print(f"✅ Extracted {len(features)} feature descriptions")
    
    # Save to JSON for integration
    output_file = "nexus_acronyms_and_features.json"
    output_data = {
        'acronyms': nexus_acronyms,
        'features': features[:50],  # Limit to first 50 features
        'analysis': {
            'total_terms': len(analysis['nexus_terms']),
            'total_features': len(features),
            'pages_analyzed': analysis['pages']
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"💾 Saved to {output_file}")
    
    # Integration recommendations
    print(f"\n🔧 Integration Recommendations:")
    print(f"1. **Nexus-Specific Acronyms**: Add Nexus acronyms to the acronym expander")
    print(f"2. **Feature-Aware Matching**: Use feature descriptions to improve matching")
    print(f"3. **Nexus Template Enhancement**: Create Nexus-specific template sections")
    print(f"4. **Context-Aware Prompts**: Include Nexus context in LLM prompts")
    print(f"5. **Model-Specific Synonyms**: Generate synonyms specific to Nexus models")
    
    # Show sample acronyms
    print(f"\n📊 Sample Nexus Acronyms for Integration:")
    sample_acronyms = list(nexus_acronyms.items())[:10]
    for acronym, data in sample_acronyms:
        print(f"   {acronym} → {data['definition']}")
    
    # Show sample features
    print(f"\n🔧 Sample Nexus Features:")
    for feature in features[:5]:
        print(f"   - {feature['text'][:80]}...")
    
    return {
        'acronyms': nexus_acronyms,
        'features': features,
        'analysis': analysis
    }


if __name__ == "__main__":
    main() 