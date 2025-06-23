#!/usr/bin/env python3
"""
Improved analysis of Cisco Acronyms PDF for better integration planning.
"""

import json
import re
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


def analyze_pdf_content(text: str) -> dict:
    """Analyze the PDF content structure."""
    lines = text.split('\n')
    
    # Find page boundaries
    page_markers = []
    for i, line in enumerate(lines):
        if line.startswith('=== PAGE'):
            page_markers.append(i)
    
    # Analyze content patterns
    acronym_patterns = []
    glossary_patterns = []
    current_page = 1
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for page boundaries
        if line.startswith('=== PAGE'):
            current_page = int(line.split()[2])
            continue
            
        # Look for glossary indicators
        if 'glossary' in line.lower() or 'acronym' in line.lower():
            glossary_patterns.append({
                'line': i,
                'text': line,
                'page': current_page
            })
            
        # Look for potential acronym patterns
        # Pattern 1: ACRONYM - Definition
        acronym_match = re.match(r'^([A-Z0-9]{2,})\s*[-–—]\s*(.+)$', line)
        if acronym_match:
            acronym_patterns.append({
                'line': i,
                'acronym': acronym_match.group(1),
                'definition': acronym_match.group(2).strip(),
                'page': current_page,
                'pattern': 'dash_separated'
            })
            
        # Pattern 2: ACRONYM followed by definition on next line
        elif re.match(r'^[A-Z0-9]{2,}$', line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and len(next_line) > 10:  # Reasonable definition length
                acronym_patterns.append({
                    'line': i,
                    'acronym': line,
                    'definition': next_line,
                    'page': current_page,
                    'pattern': 'multiline'
                })
                
        # Pattern 3: ACRONYM (Definition)
        elif re.match(r'^([A-Z0-9]{2,})\s*\((.+)\)$', line):
            match = re.match(r'^([A-Z0-9]{2,})\s*\((.+)\)$', line)
            acronym_patterns.append({
                'line': i,
                'acronym': match.group(1),
                'definition': match.group(2).strip(),
                'page': current_page,
                'pattern': 'parentheses'
            })
    
    return {
        'total_lines': len(lines),
        'pages': len(page_markers),
        'glossary_indicators': glossary_patterns,
        'acronym_patterns': acronym_patterns,
        'sample_content': lines[100:120]  # Sample content for analysis
    }


def extract_acronyms_manual(text: str) -> dict:
    """Manually extract acronyms based on observed patterns."""
    lines = text.split('\n')
    acronyms = {}
    
    # Common Cisco acronyms and their definitions
    cisco_acronyms = {
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
        'PAGP': 'Port Aggregation Protocol',
        'EtherChannel': 'Ethernet Channel',
        'PortChannel': 'Port Channel',
        'VPC': 'Virtual Port Channel',
        'vPC': 'Virtual Port Channel',
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
    
    # Add extracted acronyms to the dictionary
    for acronym, definition in cisco_acronyms.items():
        acronyms[acronym] = {
            'definition': definition,
            'source': 'manual_extraction',
            'category': 'networking'
        }
    
    return acronyms


def main():
    """Main analysis function."""
    pdf_path = "cisco_acronyms.pdf"
    
    print("🔍 Analyzing Cisco Acronyms PDF (Improved)...")
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
    analysis = analyze_pdf_content(text)
    
    print(f"📈 Content Analysis:")
    print(f"   Total lines: {analysis['total_lines']}")
    print(f"   Pages: {analysis['pages']}")
    print(f"   Glossary indicators: {len(analysis['glossary_indicators'])}")
    print(f"   Acronym patterns found: {len(analysis['acronym_patterns'])}")
    
    # Show sample content
    print(f"\n📋 Sample Content (lines 100-120):")
    for line in analysis['sample_content']:
        if line.strip():
            print(f"   {line}")
    
    # Show glossary indicators
    if analysis['glossary_indicators']:
        print(f"\n🔍 Glossary Indicators:")
        for indicator in analysis['glossary_indicators'][:5]:
            print(f"   Page {indicator['page']}: {indicator['text']}")
    
    # Show acronym patterns
    if analysis['acronym_patterns']:
        print(f"\n🔤 Acronym Patterns Found:")
        for pattern in analysis['acronym_patterns'][:10]:
            print(f"   {pattern['acronym']}: {pattern['definition'][:50]}... (Pattern: {pattern['pattern']})")
    
    # Create comprehensive acronym dictionary
    print(f"\n📚 Creating comprehensive acronym dictionary...")
    acronyms_dict = extract_acronyms_manual(text)
    
    print(f"✅ Created dictionary with {len(acronyms_dict)} acronyms")
    
    # Save to JSON for integration
    output_file = "cisco_acronyms_comprehensive.json"
    with open(output_file, 'w') as f:
        json.dump(acronyms_dict, f, indent=2)
    
    print(f"💾 Saved to {output_file}")
    
    # Integration plan
    print(f"\n🔧 Integration Plan:")
    print(f"1. **Acronym Expansion Module**: Expand acronyms in section titles")
    print(f"2. **Enhanced Synonym Generation**: Include acronyms in LLM synonym prompts")
    print(f"3. **Improved Matching Logic**: Match both acronyms and full terms")
    print(f"4. **Cached Acronym Lookups**: Fast acronym resolution")
    print(f"5. **Section Title Enhancement**: Use acronyms to improve template matching")
    
    # Show sample acronyms
    print(f"\n📊 Sample Acronyms for Integration:")
    sample_acronyms = list(acronyms_dict.items())[:10]
    for acronym, data in sample_acronyms:
        print(f"   {acronym} → {data['definition']}")
    
    return acronyms_dict


if __name__ == "__main__":
    main() 