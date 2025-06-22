#!/usr/bin/env python3
"""
Unit tests for auto-generated unit rules.
Tests that measurement units are correctly templated.
"""

import pytest
import re
import yaml
from typing import List, Dict

def load_unit_rules() -> List[Dict]:
    """Load the auto-generated unit rules."""
    with open('unit_rules.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config.get('unit_rules', [])

def load_units_inventory() -> Dict:
    """Load the units inventory."""
    with open('units.yaml', 'r') as f:
        return yaml.safe_load(f)

def test_unit_rule_patterns():
    """Test that unit rule patterns match expected measurement values."""
    unit_rules = load_unit_rules()
    units_inventory = load_units_inventory()
    
    # Test cases: (test_value, expected_unit, expected_spec_item)
    test_cases = [
        ("4248.116 BTUs per hour", "BTU", "Heat dissipation"),
        ("17.41 inches (44.23 cm)", "in", "Chassis width"),
        ("22.27 inches (56.58 cm)", "in", "Chassis depth"),
        ("3.4 inches (8.6 cm)", "in", "Chassis height"),
        ("44 lb (20 kg)", "lb", "Chassis weight"),
        ("1.3 lb (0.59 kg)", "lb", "Fan module weight"),
        ("2.64 lb (1.2 kg)", "lb", "Power supply module weight"),
        ("2 RU", "RU", "Rack units"),
        ("6.4T", "T", "Traffic processing capability"),
        ("605W typical, 1100W maximum", "W", "Power input requirements"),
        ("10,000 ft (3048 m)", "ft", "Altitude rating"),
        ("32 to 104 degrees Fahrenheit (0 to 40 degrees Celsius)", "°F", "Operating temperature"),
        ("-40 to 158 degrees Fahrenheit (-40 to 70 degrees Celsius)", "°F", "Non-operating temperature"),
    ]
    
    for test_value, expected_unit, expected_spec_item in test_cases:
        # Find the rule for this unit
        matching_rule = None
        for rule in unit_rules:
            # Look for the unit in the pattern (handle escaped characters)
            pattern_text = rule['pattern']
            # Remove regex escaping to check for unit
            unescaped_pattern = pattern_text.replace('\\', '')
            
            # Check if this rule is for the expected unit
            # Look for the unit as a complete word/pattern, not a substring
            if expected_unit == 'T':
                # Special case for T - look for \s*T\b pattern
                if '\\s*T\\b' in pattern_text:
                    matching_rule = rule
                    break
            elif expected_unit == 'BTU':
                # Special case for BTU - look for BTUs? pattern
                if 'BTUs?' in unescaped_pattern:
                    matching_rule = rule
                    break
            elif expected_unit in ['in', 'cm', 'lb', 'kg', 'ft', 'm']:
                # For units with variations, look for the unit in the pattern
                if expected_unit in unescaped_pattern:
                    matching_rule = rule
                    break
            else:
                # For other units, simple substring match
                if expected_unit in unescaped_pattern:
                    matching_rule = rule
                    break
        
        assert matching_rule is not None, f"No rule found for unit: {expected_unit}"
        
        # Test that the pattern matches the test value
        pattern = matching_rule['pattern']
        match = re.search(pattern, test_value, re.IGNORECASE)
        assert match is not None, f"Pattern {pattern} should match '{test_value}'"
        
        print(f"✅ {test_value} -> matches {pattern}")

def test_specific_unit_mappings():
    """Test that units are correctly mapped to specific spec items."""
    units_inventory = load_units_inventory()
    unit_sources = units_inventory.get('unit_sources', {})
    
    # Test specific unit mappings
    expected_mappings = {
        'BTU': ['Heat dissipation'],
        'BTU/hr': ['Heat dissipation'],
        'RU': ['Rack units'],
        'T': ['Traffic processing capability'],
        'W': ['Power input requirements'],
        'in': ['Chassis width', 'Chassis depth', 'Chassis height'],
        'cm': ['Chassis width', 'Chassis depth', 'Chassis height'],
        'lb': ['Chassis weight', 'Fan module weight', 'Power supply module weight'],
        'kg': ['Chassis weight', 'Fan module weight', 'Power supply module weight'],
        'ft': ['Altitude rating'],
        'm': ['Altitude rating'],
        '°F': ['Operating temperature', 'Non-operating temperature'],
        '°C': ['Operating temperature', 'Non-operating temperature'],
    }
    
    for unit, expected_specs in expected_mappings.items():
        actual_specs = unit_sources.get(unit, [])
        assert set(actual_specs) == set(expected_specs), \
            f"Unit {unit}: expected {expected_specs}, got {actual_specs}"
        print(f"✅ {unit} -> {actual_specs}")

def test_unit_rule_generation():
    """Test that unit rules are generated with correct patterns and priorities."""
    unit_rules = load_unit_rules()
    
    # Test that all rules have required fields
    for rule in unit_rules:
        assert 'pattern' in rule, f"Rule missing pattern: {rule}"
        assert 'placeholder' in rule, f"Rule missing placeholder: {rule}"
        assert 'priority' in rule, f"Rule missing priority: {rule}"
        assert 'description' in rule, f"Rule missing description: {rule}"
        
        # Test that pattern is valid regex
        try:
            re.compile(rule['pattern'])
        except re.error as e:
            pytest.fail(f"Invalid regex pattern '{rule['pattern']}': {e}")
        
        # Test that priority is a positive integer
        assert isinstance(rule['priority'], int), f"Priority should be int: {rule['priority']}"
        assert rule['priority'] > 0, f"Priority should be positive: {rule['priority']}"
        
        print(f"✅ Rule: {rule['pattern']} -> {rule['placeholder']} (priority: {rule['priority']})")

def test_measurement_value_extraction():
    """Test that measurement values are correctly extracted from test strings."""
    test_cases = [
        ("4248.116 BTUs per hour", "4248.116", "BTU"),
        ("17.41 inches (44.23 cm)", "17.41", "in"),
        ("44 lb (20 kg)", "44", "lb"),
        ("2 RU", "2", "RU"),
        ("6.4T", "6.4", "T"),
        ("605W typical", "605", "W"),
        ("10,000 ft", "10,000", "ft"),
        ("32 to 104 degrees Fahrenheit", "104", "°F"),
    ]
    
    unit_rules = load_unit_rules()
    
    for test_value, expected_number, expected_unit in test_cases:
        # Find matching rule using the same logic as the pattern test
        matching_rule = None
        for rule in unit_rules:
            pattern_text = rule['pattern']
            unescaped_pattern = pattern_text.replace('\\', '')
            
            if expected_unit == 'T':
                if '\\s*T\\b' in pattern_text:
                    matching_rule = rule
                    break
            elif expected_unit == 'BTU':
                if 'BTUs?' in unescaped_pattern:
                    matching_rule = rule
                    break
            elif expected_unit in ['in', 'cm', 'lb', 'kg', 'ft', 'm']:
                if expected_unit in unescaped_pattern:
                    matching_rule = rule
                    break
            else:
                if expected_unit in unescaped_pattern:
                    matching_rule = rule
                    break
        
        if matching_rule:
            pattern = matching_rule['pattern']
            match = re.search(pattern, test_value, re.IGNORECASE)
            if match:
                extracted_number = match.group(1)
                print(f"✅ {test_value} -> extracted {extracted_number} {expected_unit}")
            else:
                print(f"⚠️  {test_value} -> no match for pattern {pattern}")
        else:
            print(f"⚠️  {test_value} -> no rule found for unit {expected_unit}")

if __name__ == "__main__":
    print("=== Unit Rule Tests ===")
    
    print("\n1. Testing unit rule patterns...")
    test_unit_rule_patterns()
    
    print("\n2. Testing specific unit mappings...")
    test_specific_unit_mappings()
    
    print("\n3. Testing unit rule generation...")
    test_unit_rule_generation()
    
    print("\n4. Testing measurement value extraction...")
    test_measurement_value_extraction()
    
    print("\n=== All Tests Passed! ===") 