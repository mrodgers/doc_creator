#!/usr/bin/env python3
"""
Integrate Nexus-specific data into the adaptive matcher system.
Simplified approach for MVP - merge Nexus acronyms into existing file.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import existing modules
from ai_doc_gen.utils.llm import LLMUtility
from ai_doc_gen.utils.acronym_expander import AcronymExpander
from adaptive_llm_matcher import AdaptiveLLMMatcher


def load_nexus_data() -> Dict[str, Any]:
    """Load the extracted Nexus data."""
    try:
        with open("nexus_acronyms_and_features.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ nexus_acronyms_and_features.json not found. Run analyze_nexus_rn.py first.")
        return {}


def merge_nexus_acronyms(nexus_data: Dict[str, Any]) -> None:
    """Merge Nexus acronyms into the existing acronym file."""
    print("🔧 Merging Nexus acronyms into existing acronym file...")
    
    # Load existing acronyms
    existing_file = "cisco_acronyms_comprehensive.json"
    try:
        with open(existing_file, 'r') as f:
            existing_acronyms = json.load(f)
    except FileNotFoundError:
        print(f"❌ {existing_file} not found. Creating new file.")
        existing_acronyms = {}
    
    # Get Nexus acronyms
    nexus_acronyms = nexus_data.get('acronyms', {})
    
    # Merge acronyms (Nexus takes precedence for duplicates)
    merged_acronyms = existing_acronyms.copy()
    for acronym, data in nexus_acronyms.items():
        merged_acronyms[acronym] = data
    
    # Save merged acronyms
    with open(existing_file, 'w') as f:
        json.dump(merged_acronyms, f, indent=2)
    
    print(f"✅ Merged {len(nexus_acronyms)} Nexus acronyms into {existing_file}")
    print(f"   Total acronyms: {len(merged_acronyms)}")


def generate_nexus_synonyms(nexus_data: Dict[str, Any], llm_utility: LLMUtility) -> Dict[str, List[str]]:
    """Generate Nexus-specific synonyms using LLM."""
    print("🔤 Generating Nexus-specific synonyms...")
    
    # Get Nexus features for context
    features = nexus_data.get('features', [])
    feature_texts = [f['text'] for f in features[:5]]  # Use first 5 features
    
    # Create Nexus-specific template sections
    nexus_sections = [
        "Nexus Hardware Installation",
        "NX-OS Configuration", 
        "ACI Mode Setup",
        "Standalone Mode Configuration",
        "Fabric Extender (FEX) Installation",
        "Virtual Port Channel (vPC) Configuration",
        "VLAN Configuration",
        "VRF Setup",
        "Routing Protocol Configuration",
        "Quality of Service (QoS) Setup"
    ]
    
    synonyms = {}
    
    for section in nexus_sections:
        print(f"   Generating synonyms for: {section}")
        
        # Create enhanced prompt with Nexus context
        prompt = f"""
Generate 8-12 synonyms, abbreviations, and related terms for this Nexus hardware installation guide section:

Section: {section}

Consider:
- Nexus-specific terminology and features
- NX-OS operating system terms
- ACI and Standalone mode variations
- Hardware component names
- Configuration commands and parameters
- Common abbreviations used in Nexus documentation

Nexus Context: {', '.join(feature_texts[:2])}

Provide only the synonyms as a comma-separated list, no explanations.
"""
        
        try:
            response = llm_utility.get_completion(prompt)
            if response:
                # Parse comma-separated response
                section_synonyms = [s.strip() for s in response.split(',') if s.strip()]
                synonyms[section] = section_synonyms
                print(f"     Generated {len(section_synonyms)} synonyms")
            else:
                print(f"     ⚠️  No response for {section}")
                synonyms[section] = []
        except Exception as e:
            print(f"     ❌ Error generating synonyms for {section}: {e}")
            synonyms[section] = []
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    return synonyms


def create_nexus_template_sections() -> List[Dict[str, Any]]:
    """Create Nexus-specific template sections."""
    return [
        {
            "id": "nexus_hardware_overview",
            "title": "Nexus Hardware Overview",
            "content": "Overview of Nexus switch hardware components, specifications, and features",
            "category": "hardware",
            "priority": "high"
        },
        {
            "id": "nx_os_installation",
            "title": "NX-OS Installation and Setup",
            "content": "Installation and initial configuration of NX-OS operating system",
            "category": "software",
            "priority": "high"
        },
        {
            "id": "aci_mode_configuration",
            "title": "ACI Mode Configuration",
            "content": "Configuration for Application Centric Infrastructure mode",
            "category": "configuration",
            "priority": "medium"
        },
        {
            "id": "standalone_mode_configuration",
            "title": "Standalone Mode Configuration",
            "content": "Configuration for standalone mode operation",
            "category": "configuration",
            "priority": "medium"
        },
        {
            "id": "fex_installation",
            "title": "Fabric Extender (FEX) Installation",
            "content": "Installation and configuration of Fabric Extender modules",
            "category": "hardware",
            "priority": "medium"
        },
        {
            "id": "vpc_configuration",
            "title": "Virtual Port Channel (vPC) Configuration",
            "content": "Configuration of Virtual Port Channel for link aggregation",
            "category": "configuration",
            "priority": "high"
        },
        {
            "id": "vlan_setup",
            "title": "VLAN Configuration",
            "content": "Virtual Local Area Network configuration and management",
            "category": "configuration",
            "priority": "high"
        },
        {
            "id": "vrf_configuration",
            "title": "VRF Configuration",
            "content": "Virtual Routing and Forwarding configuration",
            "category": "configuration",
            "priority": "medium"
        },
        {
            "id": "routing_protocols",
            "title": "Routing Protocol Configuration",
            "content": "Configuration of BGP, OSPF, EIGRP, and other routing protocols",
            "category": "configuration",
            "priority": "high"
        },
        {
            "id": "qos_configuration",
            "title": "Quality of Service (QoS) Configuration",
            "content": "QoS policies, CoS, and DSCP configuration",
            "category": "configuration",
            "priority": "medium"
        }
    ]


def test_nexus_integration(nexus_data: Dict[str, Any], nexus_synonyms: Dict[str, List[str]], llm_utility: LLMUtility) -> Dict[str, Any]:
    """Test the Nexus integration with sample content."""
    print("🧪 Testing Nexus integration...")
    
    # Create test candidates with Nexus content
    test_candidates = [
        {
            "id": "nexus_9000_install",
            "title": "Cisco Nexus 9000 Series Installation Guide",
            "content": "This guide covers the installation of Nexus 9000 switches including NX-OS setup, ACI mode configuration, and vPC setup for high availability.",
            "category": "installation"
        },
        {
            "id": "nx_os_config",
            "title": "NX-OS Configuration Guide",
            "content": "Comprehensive guide for configuring NX-OS including VLAN setup, VRF configuration, routing protocols like BGP and OSPF, and QoS policies.",
            "category": "configuration"
        },
        {
            "id": "fex_guide",
            "title": "Fabric Extender Installation Guide",
            "content": "Step-by-step instructions for installing and configuring FEX modules, including UDLD setup and port channel configuration.",
            "category": "hardware"
        },
        {
            "id": "vpc_setup",
            "title": "Virtual Port Channel Configuration",
            "content": "Detailed guide for setting up vPC between Nexus switches, including LACP configuration and spanning tree considerations.",
            "category": "configuration"
        },
        {
            "id": "security_guide",
            "title": "Nexus Security Configuration",
            "content": "Security configuration including ACL setup, SSH configuration, SNMP security, and management access controls.",
            "category": "security"
        }
    ]
    
    # Create Nexus template sections
    nexus_templates = create_nexus_template_sections()
    
    # Initialize acronym expander (will now include Nexus acronyms)
    acronym_expander = AcronymExpander()
    
    # Test acronym expansion
    print("   Testing acronym expansion...")
    test_text = "Configure NX-OS with ACI mode, setup vPC, configure VLAN and VRF, enable BGP and OSPF routing protocols"
    expanded_text = acronym_expander.expand_acronyms_in_text(test_text)
    print(f"     Original: {test_text}")
    print(f"     Expanded: {expanded_text}")
    
    # Test matching with enhanced system
    print("   Testing enhanced matching...")
    matcher = AdaptiveLLMMatcher(
        templates=nexus_templates,
        llm_utility=llm_utility,
        acronym_expander=acronym_expander
    )
    
    # Add Nexus synonyms to matcher
    for section_id, synonyms in nexus_synonyms.items():
        # Find corresponding template
        for template in nexus_templates:
            if template['title'].lower() in section_id.lower():
                template['synonyms'] = synonyms
                break
    
    # Run matching
    results = []
    for candidate in test_candidates:
        matches = matcher.match_content(candidate['content'], candidate['title'])
        results.append({
            'candidate': candidate['title'],
            'matches': matches,
            'total_matches': len(matches)
        })
    
    # Calculate statistics
    total_matches = sum(r['total_matches'] for r in results)
    avg_matches = total_matches / len(results) if results else 0
    
    return {
        'test_candidates': len(test_candidates),
        'total_matches': total_matches,
        'average_matches': avg_matches,
        'results': results,
        'acronym_expansion_test': {
            'original': test_text,
            'expanded': expanded_text
        }
    }


def save_integration_results(nexus_synonyms: Dict[str, List[str]], test_results: Dict[str, Any]) -> None:
    """Save integration results to files."""
    print("💾 Saving integration results...")
    
    # Save Nexus synonyms
    with open("nexus_synonyms.json", 'w') as f:
        json.dump(nexus_synonyms, f, indent=2)
    
    # Save test results
    with open("nexus_integration_test_results.json", 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print("✅ Integration results saved")


def main():
    """Main integration function."""
    print("🔧 Integrating Nexus data into adaptive matcher system...")
    print("=" * 70)
    
    # Load Nexus data
    nexus_data = load_nexus_data()
    if not nexus_data:
        return
    
    # Initialize LLM utility
    llm_utility = LLMUtility()
    
    # Merge Nexus acronyms into existing file
    merge_nexus_acronyms(nexus_data)
    
    # Generate Nexus synonyms
    nexus_synonyms = generate_nexus_synonyms(nexus_data, llm_utility)
    
    # Test integration
    test_results = test_nexus_integration(nexus_data, nexus_synonyms, llm_utility)
    
    # Save results
    save_integration_results(nexus_synonyms, test_results)
    
    # Print summary
    print("\n📊 Integration Summary:")
    print("=" * 40)
    print(f"✅ Merged {len(nexus_data.get('acronyms', {}))} Nexus acronyms")
    print(f"✅ Generated synonyms for {len(nexus_synonyms)} Nexus sections")
    print(f"✅ Created {len(create_nexus_template_sections())} Nexus template sections")
    print(f"✅ Tested with {test_results['test_candidates']} candidates")
    print(f"✅ Achieved {test_results['total_matches']} total matches")
    print(f"✅ Average matches per candidate: {test_results['average_matches']:.1f}")
    
    # Show cache stats
    cache_stats = llm_utility.get_cache_stats()
    print(f"📈 Cache stats: {cache_stats['hits']} hits, {cache_stats['misses']} misses")
    
    print("\n🔧 Next Steps:")
    print("1. Review generated synonyms in nexus_synonyms.json")
    print("2. Test with real Nexus documentation")
    print("3. Fine-tune matching parameters")
    print("4. Validate efficacy improvements")
    
    return {
        'nexus_data': nexus_data,
        'nexus_synonyms': nexus_synonyms,
        'test_results': test_results
    }


if __name__ == "__main__":
    main() 