#!/usr/bin/env python3
"""
Expanded End-to-End Test: Larger, more realistic workflow with detailed analysis.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_doc_gen.utils.llm import LLMUtility


def calculate_confidence(candidate: str, template: str, synonyms: list) -> float:
    """Simple confidence calculation for testing."""
    candidate_lower = candidate.lower()
    template_lower = template.lower()
    
    # Exact match
    if candidate_lower == template_lower:
        return 1.0
    
    # Substring match
    if template_lower in candidate_lower or candidate_lower in template_lower:
        return 0.8
    
    # Synonym match
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


def test_end_to_end_workflow():
    """Demonstrate the complete workflow from input to output."""
    
    print("🚀 AI Document Generation System - Expanded End-to-End Test")
    print("=" * 60)
    
    # Initialize components
    print("\n1️⃣ Initializing Components...")
    llm_util = LLMUtility(cache_dir="cache", cache_ttl_hours=24)
    
    # Expanded, realistic templates
    template_sections = [
        "Power over Ethernet", "Rack Installation", "Safety Guidelines", "Network Configuration",
        "Troubleshooting", "Component Description", "Installation Instructions", "Maintenance Procedures",
        "Grounding Requirements", "LED Indicators", "Console Access", "Default Settings",
        "Firmware Upgrade", "Reset Procedures", "Environmental Requirements", "Package Contents",
        "Mounting Options", "Cable Management", "Regulatory Compliance", "Warranty Information"
    ]
    
    # Expanded, realistic and ambiguous candidates
    candidate_sections = [
        "PoE Setup and Configuration", "Mounting the device in a rack", "Electrical Safety Requirements",
        "Network Setup and IP Configuration", "Diagnostic Procedures", "Hardware Components Overview",
        "Step-by-step Installation Guide", "Regular Maintenance Schedule", "Chassis Grounding",
        "LED Status Reference", "Accessing the Console Port", "Factory Default Values",
        "Software/Firmware Update Steps", "Device Reset Instructions", "Operating Environment Specs",
        "Box Contents Checklist", "Wall Mounting Bracket Installation", "Cable Routing Best Practices",
        "Compliance and Certification", "Product Warranty Terms",
        # Ambiguous/partial matches
        "Power Supply Installation", "Fan Replacement", "System Boot Process", "User Account Setup",
        "SNMP Configuration", "Remote Management", "Physical Security", "Labeling Requirements",
        "Unboxing and Inspection", "Initial Power-On", "System Log Access"
    ]
    
    print(f"📋 Template Sections: {len(template_sections)}")
    print(f"📄 Candidate Sections: {len(candidate_sections)}")
    
    # Step 1: Generate synonyms for template sections
    print("\n2️⃣ Generating Synonyms (LLM-Powered)...")
    start_time = time.perf_counter()
    
    template_synonyms = {}
    for i, section in enumerate(template_sections, 1):
        print(f"   [{i}/{len(template_sections)}] Generating synonyms for: {section}")
        synonyms = llm_util.get_synonyms_from_llm(section)
        template_synonyms[section] = synonyms
        print(f"       → Found {len(synonyms)} synonyms: {synonyms[:3]}{'...' if len(synonyms) > 3 else ''}")
    
    synonym_time = time.perf_counter() - start_time
    print(f"   ⏱️  Synonym generation completed in {synonym_time:.2f}s")
    
    # Step 2: Check cache performance
    print("\n3️⃣ Cache Performance Analysis...")
    stats = llm_util.get_cache_stats()
    total_requests = stats['cache_hits'] + stats['cache_misses']
    hit_rate = (stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
    
    print(f"   📊 Cache Statistics:")
    print(f"      Hits: {stats['cache_hits']} (cached data)")
    print(f"      Misses: {stats['cache_misses']} (fresh LLM calls)")
    print(f"      Hit Rate: {hit_rate:.1f}%")
    print(f"      Cost Savings: {stats['cache_hits']} API calls avoided")
    
    # Step 3: Perform matching
    print("\n4️⃣ Performing Section Matching...")
    start_time = time.perf_counter()
    
    matches = []
    unmatched_candidates = []
    for candidate in candidate_sections:
        print(f"   🔍 Matching: {candidate}")
        
        # Find best match for this candidate
        best_match = None
        best_score = 0
        
        for template in template_sections:
            # Use the matcher to get confidence score
            confidence = calculate_confidence(candidate, template, template_synonyms.get(template, []))
            
            if confidence > best_score:
                best_score = confidence
                best_match = template
        
        if best_match and best_score > 0.3:  # Threshold for meaningful match
            matches.append({
                'candidate': candidate,
                'template': best_match,
                'confidence': best_score
            })
            print(f"      ✅ Matched to: {best_match} (confidence: {best_score:.2f})")
        else:
            unmatched_candidates.append(candidate)
            print(f"      ❌ No good match found (best: {best_score:.2f})")
    
    matching_time = time.perf_counter() - start_time
    print(f"   ⏱️  Matching completed in {matching_time:.2f}s")
    
    # Step 4: Generate results and analysis
    print("\n5️⃣ Results Analysis...")
    
    # Calculate coverage
    matched_templates = set(match['template'] for match in matches)
    coverage = len(matched_templates) / len(template_sections) * 100
    
    print(f"   📈 Coverage Analysis:")
    print(f"      Templates Matched: {len(matched_templates)}/{len(template_sections)}")
    print(f"      Coverage: {coverage:.1f}%")
    print(f"      Candidates Matched: {len(matches)}/{len(candidate_sections)}")
    
    # Detailed match summary
    perfect_matches = [m for m in matches if m['confidence'] >= 0.95]
    partial_matches = [m for m in matches if 0.5 <= m['confidence'] < 0.95]
    weak_matches = [m for m in matches if 0.3 < m['confidence'] < 0.5]
    print(f"\n   📊 Match Quality Summary:")
    print(f"      Perfect Matches (>=0.95): {len(perfect_matches)}")
    print(f"      Partial Matches (0.5-0.95): {len(partial_matches)}")
    print(f"      Weak Matches (0.3-0.5): {len(weak_matches)}")
    print(f"      Unmatched Candidates: {len(unmatched_candidates)}")
    
    # Show a few unmatched candidates and templates
    if unmatched_candidates:
        print(f"\n   ⚠️  Example Unmatched Candidates:")
        for c in unmatched_candidates[:5]:
            print(f"      - {c}")
    unmatched_templates = set(template_sections) - matched_templates
    if unmatched_templates:
        print(f"\n   ⚠️  Example Unmatched Templates:")
        for t in list(unmatched_templates)[:5]:
            print(f"      - {t}")
    
    # Step 5: Performance summary
    print("\n6️⃣ Performance Summary...")
    total_time = synonym_time + matching_time
    
    print(f"   ⏱️  Total Processing Time: {total_time:.2f}s")
    print(f"   🚀 Average Time per Section: {total_time/len(template_sections):.2f}s")
    print(f"   💰 API Calls Made: {stats['cache_misses']}")
    print(f"   💾 Cache Efficiency: {hit_rate:.1f}%")
    
    # Step 6: Recommendations
    print("\n7️⃣ Recommendations...")
    
    if coverage < 70:
        print(f"   🔧 Low coverage ({coverage:.1f}%) - Consider:")
        print(f"      - Adding more synonyms to templates")
        print(f"      - Using LLM-powered matching for ambiguous cases")
        print(f"      - Expanding template vocabulary")
    
    if hit_rate < 50:
        print(f"   🔧 Low cache hit rate ({hit_rate:.1f}%) - Consider:")
        print(f"      - Increasing cache TTL")
        print(f"      - Processing similar documents together")
    
    if len(unmatched_templates) > 0:
        print(f"   🔧 {len(unmatched_templates)} unmatched templates - Consider:")
        print(f"      - Adding more candidate sections")
        print(f"      - Adjusting matching thresholds")
        print(f"      - Using LLM for semantic matching")
    
    print("\n✅ Expanded End-to-End Test Completed Successfully!")
    return {
        'coverage': coverage,
        'cache_hit_rate': hit_rate,
        'total_time': total_time,
        'matches': matches,
        'unmatched_templates': list(unmatched_templates),
        'unmatched_candidates': unmatched_candidates
    }


if __name__ == "__main__":
    try:
        results = test_end_to_end_workflow()
        print(f"\n📊 Final Results:")
        print(f"   Coverage: {results['coverage']:.1f}%")
        print(f"   Cache Hit Rate: {results['cache_hit_rate']:.1f}%")
        print(f"   Processing Time: {results['total_time']:.2f}s")
        print(f"   Successful Matches: {len(results['matches'])}")
        print(f"   Unmatched Candidates: {len(results['unmatched_candidates'])}")
        print(f"   Unmatched Templates: {len(results['unmatched_templates'])}")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 