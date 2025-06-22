#!/usr/bin/env python3
"""
Generate synonyms and abbreviations for template sections using LLM.
This script creates a comprehensive synonym dictionary for improved matching.
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_doc_gen.utils.llm import llm_utility


def load_template_sections(template_path: str) -> list:
    """Load template section titles from the template file."""
    try:
        with open(template_path, 'r') as f:
            template = json.load(f)
        
        # Extract section titles from template structure
        sections = template.get('template_structure', {}).get('section_hierarchy', [])
        titles = []
        
        def extract_titles(section_list):
            for section in section_list:
                if isinstance(section, dict):
                    if 'title' in section:
                        titles.append(section['title'])
                    if 'subsections' in section:
                        extract_titles(section['subsections'])
                elif isinstance(section, str):
                    titles.append(section)
        
        extract_titles(sections)
        return titles
        
    except Exception as e:
        print(f"Error loading template: {e}")
        return []


def generate_synonym_dictionary(template_path: str, output_path: str = "section_synonyms.json"):
    """Generate synonyms for all template sections."""
    print("🔍 Loading template sections...")
    template_titles = load_template_sections(template_path)
    
    if not template_titles:
        print("❌ No template sections found")
        return
    
    print(f"📋 Found {len(template_titles)} template sections")
    print("🚀 Generating synonyms using LLM...")
    
    synonym_dict = {
        'metadata': {
            'template_path': template_path,
            'total_sections': len(template_titles),
            'generation_timestamp': str(Path(__file__).stat().st_mtime),
            'model': 'gpt-4',
            'temperature': 0.2
        },
        'synonyms': {}
    }
    
    for i, title in enumerate(template_titles, 1):
        print(f"  [{i}/{len(template_titles)}] Generating synonyms for: {title}")
        
        synonyms = llm_utility.get_synonyms_from_llm(title)
        synonym_dict['synonyms'][title] = synonyms
        
        print(f"     ✅ Found {len(synonyms)} synonyms: {synonyms}")
    
    # Save the complete dictionary
    with open(output_path, 'w') as f:
        json.dump(synonym_dict, f, indent=2)
    
    print(f"\n✅ Synonym dictionary saved to: {output_path}")
    print(f"📊 Summary:")
    print(f"   Total sections: {len(template_titles)}")
    print(f"   Total synonyms: {sum(len(syns) for syns in synonym_dict['synonyms'].values())}")
    print(f"   Average synonyms per section: {sum(len(syns) for syns in synonym_dict['synonyms'].values()) / len(template_titles):.1f}")


def main():
    """Main function."""
    print("🚀 Section Synonym Generator")
    print("=" * 50)
    
    # Template path
    template_path = "c8500_superset_template.json"
    
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        print("   Run llm_superset_template_generator.py first to create the template")
        return
    
    # Generate synonyms
    generate_synonym_dictionary(template_path)
    
    print("\n🎯 Synonym generation complete!")
    print("   Next: Integrate the synonym dictionary into your matcher")


if __name__ == "__main__":
    main() 