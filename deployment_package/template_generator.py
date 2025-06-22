# -------------------------
# template_generator.py
# -------------------------
"""
This script reads:
  - chapter1_overview.json (structured chapter JSON)
  - extracted_specs.json  (list of spec items and values)
  - template_rules.yaml   (config-driven spec patterns)
It dynamically generates generic patterns based on spec units,
merges with config rules, applies replacements via regex with
word boundaries, and outputs chapter1_template.json.
"""

import json
import copy
import re
import yaml
import logging
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load utilities
def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# Generate generic regex patterns from spec list
UNIT_PATTERN = re.compile(r"([\d\.]+)\s*([^\d\s]+)")

def generate_generic_rules(specs):
    rules = []
    for spec in specs:
        val = spec['value']
        m = UNIT_PATTERN.search(val)
        if not m:
            continue
        number, unit = m.groups()
        # escape unit for regex
        unit_esc = re.escape(unit)
        # pattern matches number + optional space + unit
        pat = rf"\b{re.escape(number)}\s*{unit_esc}\b"
        rules.append({
            'pattern': pat,
            'placeholder': f"{{{{{spec['spec_item']}}}}}",
            'priority': len(pat)
        })
    return rules

# Recursively replace values in JSON structure
PAGE_REF = re.compile(r'^(Page\s+\d+(\s+of\s+\d+)?)$', re.IGNORECASE)

def replace_in_obj(obj, all_rules):
    if isinstance(obj, dict):
        return {k: replace_in_obj(v, all_rules) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_in_obj(v, all_rules) for v in obj]
    if isinstance(obj, str):
        if PAGE_REF.match(obj.strip()):
            return obj
        text = obj
        # apply rules in descending priority (longer patterns first)
        for rule in sorted(all_rules, key=lambda r: r.get('priority',0), reverse=True):
            text, count = re.subn(rule['pattern'], rule['placeholder'], text)
            if count:
                logger.info(f"Applied rule {rule.get('pattern')} -> {rule['placeholder']} ({count} replacements)")
        return text
    return obj

def load_template_rules(config_file: str) -> List[Dict[str, Any]]:
    """Load template rules from YAML config file."""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('rules', [])

def load_unit_rules(unit_rules_file: str) -> List[Dict[str, Any]]:
    """Load auto-generated unit rules from YAML file."""
    try:
        with open(unit_rules_file, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('unit_rules', [])
    except FileNotFoundError:
        logger.warning(f"Unit rules file {unit_rules_file} not found. Skipping unit rules.")
        return []

def create_specific_unit_rules(extracted_specs: List[Dict], unit_rules: List[Dict]) -> List[Dict]:
    """Create specific unit rules by mapping units to actual spec items."""
    specific_rules = []
    
    # Load units inventory to map units to spec items
    try:
        with open('units.yaml', 'r') as f:
            units_data = yaml.safe_load(f)
        unit_sources = units_data.get('unit_sources', {})
    except FileNotFoundError:
        logger.warning("units.yaml not found. Using generic unit rules.")
        return unit_rules
    
    # Create a mapping of spec items to their values for unit detection
    spec_values = {spec['spec_item']: spec['value'] for spec in extracted_specs}
    
    for unit_rule in unit_rules:
        pattern = unit_rule['pattern']
        unit = extract_unit_from_pattern(pattern)
        
        # Find which spec items use this unit
        if unit in unit_sources:
            for spec_item in unit_sources[unit]:
                # Create a specific rule for this unit + spec combination
                specific_rule = {
                    'pattern': pattern,
                    'placeholder': f'{{{{{spec_item}}}}}',
                    'priority': unit_rule['priority'],
                    'description': f'Unit rule for {spec_item} ({unit})'
                }
                specific_rules.append(specific_rule)
        else:
            # Keep the generic rule if no specific mapping found
            specific_rules.append(unit_rule)
    
    return specific_rules

def extract_unit_from_pattern(pattern: str) -> str:
    """Extract the unit from a regex pattern."""
    # Pattern is like: (\d+(?:\.\d+)?)\s*BTU\b
    # We want to extract "BTU"
    match = re.search(r'\\s\*([^\\]+)\\b', pattern)
    if match:
        return match.group(1)
    return ""

def merge_rules(existing_rules: List[Dict], unit_rules: List[Dict]) -> List[Dict]:
    """Merge existing rules with unit rules, giving priority to existing rules."""
    # Create a set of existing patterns to avoid duplicates
    existing_patterns = {rule['pattern'] for rule in existing_rules}
    
    # Add unit rules that don't conflict with existing patterns
    merged_rules = existing_rules.copy()
    for unit_rule in unit_rules:
        if unit_rule['pattern'] not in existing_patterns:
            merged_rules.append(unit_rule)
            logger.info(f"Added unit rule: {unit_rule['pattern']} -> {unit_rule['placeholder']}")
    
    # Sort by priority (higher priority first)
    merged_rules.sort(key=lambda x: x.get('priority', 0), reverse=True)
    
    return merged_rules

def apply_template_rules(chapter_data: Dict, rules: List[Dict]) -> Dict:
    """Apply template rules to chapter content."""
    return replace_in_obj(copy.deepcopy(chapter_data), rules)

def main():
    """Main function to generate templates from extracted specifications."""
    
    # Load extracted specifications
    with open("extracted_specs.json", "r") as f:
        extracted_specs = json.load(f)
    
    # Load chapter content
    with open("chapter1_overview.json", "r") as f:
        chapter_data = json.load(f)
    
    # Load existing template rules
    existing_rules = load_template_rules("template_rules.yaml")
    logger.info(f"Loaded {len(existing_rules)} existing template rules")
    
    # Load auto-generated unit rules
    unit_rules = load_unit_rules("unit_rules.yaml")
    logger.info(f"Loaded {len(unit_rules)} unit rules")
    
    # Create specific unit rules by mapping units to spec items
    specific_unit_rules = create_specific_unit_rules(extracted_specs, unit_rules)
    logger.info(f"Created {len(specific_unit_rules)} specific unit rules")
    
    # Merge existing rules with unit rules
    all_rules = merge_rules(existing_rules, specific_unit_rules)
    logger.info(f"Total rules after merging: {len(all_rules)}")
    
    # Apply rules to create templates
    templated_content = apply_template_rules(chapter_data, all_rules)
    
    # Save templated content
    save_json(templated_content, 'chapter1_template.json')
    logger.info("✅ Templated chapter saved to chapter1_template.json")

if __name__ == '__main__':
    main()
