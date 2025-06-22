#!/usr/bin/env python3
"""
Simplified Nexus integration test for MVP.
Tests acronym expansion and basic functionality without complex matching.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import existing modules
from ai_doc_gen.utils.llm import LLMUtility
from ai_doc_gen.utils.acronym_expander import AcronymExpander


def test_nexus_acronym_expansion():
    """Test Nexus acronym expansion functionality."""
    print("🧪 Testing Nexus acronym expansion...")
    
    # Initialize acronym expander (should now include Nexus acronyms)
    acronym_expander = AcronymExpander()
    
    # Test cases with Nexus-specific content
    test_cases = [
        {
            "text": "Configure NX-OS with ACI mode, setup vPC, configure VLAN and VRF, enable BGP and OSPF routing protocols",
            "description": "Nexus configuration commands"
        },
        {
            "text": "Install FEX modules and configure UDLD for link detection",
            "description": "Fabric Extender installation"
        },
        {
            "text": "Setup QoS policies with CoS and DSCP for traffic prioritization",
            "description": "Quality of Service configuration"
        },
        {
            "text": "Configure SNMP, Syslog, and SSH for management access",
            "description": "Management and monitoring"
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases):
        print(f"\n   Test {i+1}: {test_case['description']}")
        print(f"   Original: {test_case['text']}")
        
        # Expand acronyms
        expanded = acronym_expander.expand_acronyms_in_text(test_case['text'])
        print(f"   Expanded: {expanded}")
        
        # Find acronyms in text
        found_acronyms = acronym_expander.find_acronyms_in_text(test_case['text'])
        print(f"   Found acronyms: {found_acronyms}")
        
        # Get synonyms
        synonyms = acronym_expander.get_acronym_synonyms(test_case['text'])
        print(f"   Synonyms: {synonyms[:5]}...")  # Show first 5
        
        results.append({
            'test_case': test_case['description'],
            'original': test_case['text'],
            'expanded': expanded,
            'found_acronyms': found_acronyms,
            'synonyms_count': len(synonyms)
        })
    
    return results


def test_nexus_synonym_generation():
    """Test Nexus-specific synonym generation."""
    print("\n🔤 Testing Nexus synonym generation...")
    
    # Initialize LLM utility
    llm_utility = LLMUtility()
    
    # Test Nexus-specific sections
    nexus_sections = [
        "Nexus Hardware Installation",
        "NX-OS Configuration",
        "ACI Mode Setup",
        "Virtual Port Channel Configuration"
    ]
    
    synonyms_results = {}
    
    for section in nexus_sections:
        print(f"   Generating synonyms for: {section}")
        
        try:
            # Use the correct method name
            synonyms = llm_utility.get_synonyms_from_llm(section)
            synonyms_results[section] = synonyms
            print(f"     Generated {len(synonyms)} synonyms")
        except Exception as e:
            print(f"     ❌ Error: {e}")
            synonyms_results[section] = []
    
    return synonyms_results


def test_nexus_template_matching():
    """Test basic template matching with Nexus content."""
    print("\n📋 Testing Nexus template matching...")
    
    # Create simple Nexus template sections
    nexus_templates = [
        {
            "id": "nexus_hardware",
            "title": "Nexus Hardware Installation",
            "content": "Overview of Nexus switch hardware components, specifications, and features",
            "category": "hardware"
        },
        {
            "id": "nx_os_config",
            "title": "NX-OS Configuration",
            "content": "Installation and initial configuration of NX-OS operating system",
            "category": "software"
        },
        {
            "id": "aci_mode",
            "title": "ACI Mode Configuration",
            "content": "Configuration for Application Centric Infrastructure mode",
            "category": "configuration"
        },
        {
            "id": "vpc_config",
            "title": "Virtual Port Channel Configuration",
            "content": "Configuration of Virtual Port Channel for link aggregation",
            "category": "configuration"
        }
    ]
    
    # Test candidates with Nexus content
    test_candidates = [
        {
            "title": "Cisco Nexus 9000 Series Installation Guide",
            "content": "This guide covers the installation of Nexus 9000 switches including NX-OS setup, ACI mode configuration, and vPC setup for high availability.",
            "expected_matches": ["nexus_hardware", "nx_os_config", "aci_mode", "vpc_config"]
        },
        {
            "title": "NX-OS Configuration Guide",
            "content": "Comprehensive guide for configuring NX-OS including VLAN setup, VRF configuration, routing protocols like BGP and OSPF, and QoS policies.",
            "expected_matches": ["nx_os_config"]
        },
        {
            "title": "Fabric Extender Installation Guide",
            "content": "Step-by-step instructions for installing and configuring FEX modules, including UDLD setup and port channel configuration.",
            "expected_matches": ["nexus_hardware"]
        }
    ]
    
    # Simple keyword-based matching for MVP
    matching_results = []
    
    for candidate in test_candidates:
        print(f"\n   Testing: {candidate['title']}")
        
        matches = []
        for template in nexus_templates:
            # Simple keyword matching
            template_keywords = template['title'].lower().split() + template['content'].lower().split()
            candidate_text = (candidate['title'] + " " + candidate['content']).lower()
            
            # Count keyword matches
            match_count = sum(1 for keyword in template_keywords if keyword in candidate_text)
            if match_count > 0:
                confidence = min(match_count / len(template_keywords), 1.0)
                matches.append({
                    'template_id': template['id'],
                    'template_title': template['title'],
                    'confidence': confidence,
                    'match_count': match_count
                })
        
        # Sort by confidence
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"     Found {len(matches)} matches:")
        for match in matches[:3]:  # Show top 3
            print(f"       - {match['template_title']} (confidence: {match['confidence']:.2f})")
        
        matching_results.append({
            'candidate': candidate['title'],
            'matches': matches,
            'expected_matches': candidate['expected_matches']
        })
    
    return matching_results


def calculate_coverage_metrics(matching_results):
    """Calculate coverage metrics from matching results."""
    print("\n📊 Calculating coverage metrics...")
    
    total_candidates = len(matching_results)
    candidates_with_matches = sum(1 for result in matching_results if result['matches'])
    total_matches = sum(len(result['matches']) for result in matching_results)
    
    coverage_percentage = (candidates_with_matches / total_candidates) * 100 if total_candidates > 0 else 0
    avg_matches_per_candidate = total_matches / total_candidates if total_candidates > 0 else 0
    
    print(f"   Total candidates: {total_candidates}")
    print(f"   Candidates with matches: {candidates_with_matches}")
    print(f"   Total matches: {total_matches}")
    print(f"   Coverage: {coverage_percentage:.1f}%")
    print(f"   Average matches per candidate: {avg_matches_per_candidate:.1f}")
    
    return {
        'total_candidates': total_candidates,
        'candidates_with_matches': candidates_with_matches,
        'total_matches': total_matches,
        'coverage_percentage': coverage_percentage,
        'avg_matches_per_candidate': avg_matches_per_candidate
    }


def main():
    """Main test function."""
    print("🔧 Simplified Nexus Integration Test")
    print("=" * 50)
    
    # Test 1: Acronym expansion
    acronym_results = test_nexus_acronym_expansion()
    
    # Test 2: Synonym generation
    synonym_results = test_nexus_synonym_generation()
    
    # Test 3: Template matching
    matching_results = test_nexus_template_matching()
    
    # Calculate metrics
    coverage_metrics = calculate_coverage_metrics(matching_results)
    
    # Save results
    test_results = {
        'acronym_expansion': acronym_results,
        'synonym_generation': synonym_results,
        'template_matching': matching_results,
        'coverage_metrics': coverage_metrics,
        'timestamp': str(Path().cwd())
    }
    
    with open("nexus_integration_simple_test_results.json", 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Results saved to nexus_integration_simple_test_results.json")
    
    # Print summary
    print(f"\n📈 Test Summary:")
    print(f"   Acronym expansion tests: {len(acronym_results)}")
    print(f"   Synonym generation tests: {len(synonym_results)}")
    print(f"   Template matching tests: {len(matching_results)}")
    print(f"   Coverage: {coverage_metrics['coverage_percentage']:.1f}%")
    
    # Check cache stats
    llm_utility = LLMUtility()
    cache_stats = llm_utility.get_cache_stats()
    print(f"   Cache stats: {cache_stats.get('cache_hits', 0)} hits, {cache_stats.get('cache_misses', 0)} misses")
    
    return test_results


if __name__ == "__main__":
    main() 