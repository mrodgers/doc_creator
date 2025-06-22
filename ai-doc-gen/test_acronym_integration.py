#!/usr/bin/env python3
"""
Test Acronym Integration: Demonstrate how Cisco acronyms improve matching performance.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_doc_gen.utils.llm import LLMUtility
from ai_doc_gen.utils.acronym_expander import AcronymExpander, create_enhanced_synonym_prompt


def test_acronym_integration():
    """Test the integration of acronym expansion into the system."""
    
    print("🔤 Acronym Integration Test")
    print("=" * 50)
    
    # Initialize components
    print("\n1️⃣ Initializing Components...")
    llm_util = LLMUtility(cache_dir="cache", cache_ttl_hours=24)
    acronym_expander = AcronymExpander()
    
    # Test cases with acronyms
    test_titles = [
        "PoE Configuration",
        "VLAN Setup and Management", 
        "QoS Configuration",
        "SNMP Management",
        "BGP Routing Configuration",
        "OSPF Network Setup",
        "STP Configuration",
        "MPLS VPN Setup",
        "IPSec Tunnel Configuration",
        "DHCP Server Setup"
    ]
    
    print(f"📋 Testing {len(test_titles)} titles with acronyms")
    
    # Test 1: Acronym expansion
    print("\n2️⃣ Testing Acronym Expansion...")
    for title in test_titles[:5]:  # Test first 5
        enhanced = acronym_expander.enhance_section_title(title)
        print(f"   📋 {title}")
        print(f"      Expanded: {enhanced['expanded']}")
        print(f"      Acronyms: {enhanced['acronyms_found']}")
        print(f"      Synonyms: {enhanced['synonyms'][:3]}...")
    
    # Test 2: Enhanced synonym generation
    print("\n3️⃣ Testing Enhanced Synonym Generation...")
    start_time = time.perf_counter()
    
    enhanced_synonyms = {}
    for title in test_titles:
        print(f"   🔍 Generating synonyms for: {title}")
        synonyms = llm_util.get_synonyms_from_llm(title)
        enhanced_synonyms[title] = synonyms
        print(f"      → Found {len(synonyms)} synonyms: {synonyms[:3]}{'...' if len(synonyms) > 3 else ''}")
    
    synonym_time = time.perf_counter() - start_time
    print(f"   ⏱️  Synonym generation completed in {synonym_time:.2f}s")
    
    # Test 3: Cache performance
    print("\n4️⃣ Cache Performance Analysis...")
    stats = llm_util.get_cache_stats()
    total_requests = stats['cache_hits'] + stats['cache_misses']
    hit_rate = (stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
    
    print(f"   📊 Cache Statistics:")
    print(f"      Hits: {stats['cache_hits']} (cached data)")
    print(f"      Misses: {stats['cache_misses']} (fresh LLM calls)")
    print(f"      Hit Rate: {hit_rate:.1f}%")
    
    # Test 4: Matching improvement demonstration
    print("\n5️⃣ Matching Improvement Demonstration...")
    
    # Test cases with and without acronyms
    test_candidates = [
        "Power over Ethernet Setup",  # Should match "PoE Configuration"
        "Virtual Local Area Network Management",  # Should match "VLAN Setup and Management"
        "Quality of Service Setup",  # Should match "QoS Configuration"
        "Simple Network Management Protocol Configuration",  # Should match "SNMP Management"
        "Border Gateway Protocol Setup",  # Should match "BGP Routing Configuration"
        "Open Shortest Path First Configuration",  # Should match "OSPF Network Setup"
        "Spanning Tree Protocol Setup",  # Should match "STP Configuration"
        "Multiprotocol Label Switching Configuration",  # Should match "MPLS VPN Setup"
        "Internet Protocol Security Configuration",  # Should match "IPSec Tunnel Configuration"
        "Dynamic Host Configuration Protocol Setup"  # Should match "DHCP Server Setup"
    ]
    
    def calculate_confidence_with_acronyms(candidate: str, template: str, synonyms: list) -> float:
        """Calculate confidence with acronym enhancement."""
        candidate_lower = candidate.lower()
        template_lower = template.lower()
        
        # Exact match
        if candidate_lower == template_lower:
            return 1.0
        
        # Substring match
        if template_lower in candidate_lower or candidate_lower in template_lower:
            return 0.8
        
        # Synonym match (including acronyms)
        for synonym in synonyms:
            if synonym.lower() in candidate_lower:
                return 0.7
        
        # Word overlap
        candidate_words = set(candidate_lower.split())
        template_words = set(template_lower.split())
        overlap = len(candidate_words & template_words)
        total = len(candidate_words | template_words)
        
        if total > 0:
            return overlap / total * 0.6
        
        return 0.0
    
    # Test matching with acronym enhancement
    matches = []
    for candidate in test_candidates:
        best_match = None
        best_score = 0
        
        for template in test_titles:
            synonyms = enhanced_synonyms.get(template, [])
            confidence = calculate_confidence_with_acronyms(candidate, template, synonyms)
            
            if confidence > best_score:
                best_score = confidence
                best_match = template
        
        if best_match and best_score > 0.3:
            matches.append({
                'candidate': candidate,
                'template': best_match,
                'confidence': best_score
            })
            print(f"   ✅ {candidate}")
            print(f"      → {best_match} (confidence: {best_score:.2f})")
        else:
            print(f"   ❌ {candidate} (best: {best_score:.2f})")
    
    # Test 5: Performance comparison
    print("\n6️⃣ Performance Comparison...")
    
    # Calculate coverage
    matched_templates = set(match['template'] for match in matches)
    coverage = len(matched_templates) / len(test_titles) * 100
    
    print(f"   📈 Results:")
    print(f"      Templates Matched: {len(matched_templates)}/{len(test_titles)}")
    print(f"      Coverage: {coverage:.1f}%")
    print(f"      Candidates Matched: {len(matches)}/{len(test_candidates)}")
    
    # Show acronym statistics
    acronym_stats = acronym_expander.get_acronym_statistics()
    print(f"\n   📊 Acronym Statistics:")
    print(f"      Total acronyms: {acronym_stats['total_acronyms']}")
    print(f"      Categories: {acronym_stats['categories']}")
    
    # Test 6: Enhanced prompt demonstration
    print("\n7️⃣ Enhanced Prompt Demonstration...")
    sample_title = "PoE Configuration"
    enhanced_prompt = create_enhanced_synonym_prompt(sample_title, acronym_expander)
    print(f"   📝 Enhanced prompt for '{sample_title}':")
    print(f"      {enhanced_prompt[:200]}...")
    
    print("\n✅ Acronym Integration Test Completed Successfully!")
    
    return {
        'coverage': coverage,
        'cache_hit_rate': hit_rate,
        'total_acronyms': acronym_stats['total_acronyms'],
        'matches': matches,
        'processing_time': synonym_time
    }


if __name__ == "__main__":
    try:
        results = test_acronym_integration()
        print(f"\n📊 Final Results:")
        print(f"   Coverage: {results['coverage']:.1f}%")
        print(f"   Cache Hit Rate: {results['cache_hit_rate']:.1f}%")
        print(f"   Total Acronyms: {results['total_acronyms']}")
        print(f"   Processing Time: {results['processing_time']:.2f}s")
        print(f"   Successful Matches: {len(results['matches'])}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 