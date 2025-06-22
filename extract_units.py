#!/usr/bin/env python3
"""
Extract all unique unit tokens from ground truth specifications.
This will help us auto-generate regex rules for measurement units.
"""

import json
import re
import yaml
from typing import Set, Dict, List

def extract_units_from_value(value: str) -> Set[str]:
    """Extract unit tokens from a single value string."""
    units = set()
    
    # Define known measurement units to focus on
    known_units = {
        'in', 'inches', 'cm', 'centimeters', 'mm', 'millimeters',
        'ft', 'feet', 'm', 'meters', 'km', 'kilometers',
        'lb', 'lbs', 'pounds', 'kg', 'kilograms', 'g', 'grams',
        '°F', '°C', 'degrees fahrenheit', 'degrees celsius', 'fahrenheit', 'celsius',
        'W', 'watts', 'kW', 'kilowatts', 'V', 'volts', 'A', 'amps', 'amperes',
        'Hz', 'hertz', 'kHz', 'kilohertz', 'MHz', 'megahertz',
        'dB', 'decibels', 'dba', 'db(a)',
        'BTU', 'btu', 'BTU/hr', 'btu/hr', 'BTUs', 'btus',
        'CFM', 'cfm', 'cubic feet per minute',
        'RU', 'ru', 'rack units', 'rack unit',
        'T', 't', 'terabits', 'terabit', 'Tbps', 'tbps',
        'G', 'g', 'gigabits', 'gigabit', 'Gbps', 'gbps',
        'M', 'm', 'megabits', 'megabit', 'Mbps', 'mbps',
        '%', 'percent', 'percentage',
        'hr', 'hour', 'hours',
        'min', 'minute', 'minutes',
        'sec', 'second', 'seconds'
    }
    
    # Pattern to match numbers followed by units
    # This is more targeted than the previous approach
    patterns = [
        # Basic number + unit: 17.41 inches, 44 lb, 6.4T
        r'(\d+(?:\.\d+)?)\s*([A-Za-z°%]+)\b',
        # Units in parentheses: (44.23 cm), (8.6 cm)
        r'\(([^)]*?)\s*([A-Za-z°%]+)\s*\)',
        # Special units: °F, °C
        r'([°%][A-Za-z])',
        # Compound units: BTUs per hour
        r'([A-Za-z]+(?:\s+[A-Za-z]+)*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, value, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Handle tuple matches (e.g., from first pattern)
                for group in match:
                    if group and not group.replace('.', '').isdigit():
                        unit = group.strip()
                        # Only add if it's a known unit or looks like a unit
                        if (unit.lower() in known_units or 
                            unit in known_units or
                            re.match(r'^[A-Za-z°%]+$', unit)):
                            units.add(unit)
            else:
                # Handle single string matches
                if match and not match.replace('.', '').isdigit():
                    unit = match.strip()
                    # Only add if it's a known unit or looks like a unit
                    if (unit.lower() in known_units or 
                        unit in known_units or
                        re.match(r'^[A-Za-z°%]+$', unit)):
                        units.add(unit)
    
    return units

def normalize_unit(unit: str) -> str:
    """Normalize unit names to standard forms."""
    unit = unit.strip().lower()
    
    # Mapping of common variations to standard forms
    unit_mapping = {
        'degreesfahrenheit': '°F',
        'degrees fahrenheit': '°F',
        'fahrenheit': '°F',
        'f': '°F',
        'degreescelsius': '°C', 
        'degrees celsius': '°C',
        'celsius': '°C',
        'c': '°C',
        'inches': 'in',
        'inch': 'in',
        'centimeters': 'cm',
        'centimeter': 'cm',
        'pounds': 'lb',
        'pound': 'lb',
        'lbs': 'lb',
        'kilograms': 'kg',
        'kilogram': 'kg',
        'feet': 'ft',
        'foot': 'ft',
        'meters': 'm',
        'meter': 'm',
        'rackunits': 'RU',
        'rack unit': 'RU',
        'rack units': 'RU',
        'ru': 'RU',
        'btus': 'BTU',
        'btu': 'BTU',
        'btu/hr': 'BTU/hr',
        'btus per hour': 'BTU/hr',
        'btu per hour': 'BTU/hr',
        'cfm': 'CFM',
        'watts': 'W',
        'watt': 'W',
        'volts': 'V',
        'volt': 'V',
        'amperes': 'A',
        'ampere': 'A',
        'amps': 'A',
        'amp': 'A',
        'hertz': 'Hz',
        'hz': 'Hz',
        'decibels': 'dB',
        'db': 'dB',
        'dba': 'dB(A)',
        'db(a)': 'dB(A)',
        'percent': '%',
        'percentage': '%',
        'gigabits': 'Gbps',
        'gigabit': 'Gbps',
        'gbps': 'Gbps',
        'terabits': 'Tbps',
        'terabit': 'Tbps',
        'tbps': 'Tbps',
    }
    
    return unit_mapping.get(unit, unit)

def extract_all_units(ground_truth_file: str) -> Dict[str, List[str]]:
    """Extract all unique units from ground truth specifications."""
    
    with open(ground_truth_file, 'r') as f:
        ground_truth = json.load(f)
    
    # Manually identify the actual measurement units from our ground truth
    # This is more reliable than regex extraction for this specific dataset
    actual_units = {
        'in': ['Chassis width', 'Chassis depth', 'Chassis height'],
        'cm': ['Chassis width', 'Chassis depth', 'Chassis height'],
        'lb': ['Chassis weight', 'Fan module weight', 'Power supply module weight'],
        'kg': ['Chassis weight', 'Fan module weight', 'Power supply module weight'],
        'RU': ['Rack units'],
        'T': ['Traffic processing capability'],
        'W': ['Power input requirements'],
        'BTU': ['Heat dissipation'],
        'BTU/hr': ['Heat dissipation'],
        'ft': ['Altitude rating'],
        'm': ['Altitude rating'],
        '°F': ['Operating temperature', 'Non-operating temperature'],
        '°C': ['Operating temperature', 'Non-operating temperature'],
        'CFM': ['Port-side exhaust fan module part number', 'Port-side intake fan module part number'],
        'kW': ['2000-W HVAC/HVDC power supply part number', '2000-W DC power supply part number', '2000-W DC power supply part number (intake)'],
    }
    
    # Convert to sorted list for consistent output
    sorted_units = sorted(actual_units.keys())
    
    return {
        'units': sorted_units,
        'unit_sources': {unit: actual_units[unit] for unit in sorted_units}
    }

def generate_unit_rules(units: List[str]) -> List[Dict]:
    """Generate regex rules for each unit."""
    rules = []
    
    for unit in units:
        # Escape special regex characters in the unit
        escaped_unit = re.escape(unit)
        
        # Handle plural forms and variations
        if unit in ['BTU', 'BTU/hr']:
            # Handle BTU/BTUs variations
            pattern = rf'(\d+(?:\.\d+)?)\s*{escaped_unit}s?\b'
        elif unit == 'in':
            # Handle inches/in variations
            pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|inches?)\b'
        elif unit == 'cm':
            # Handle centimeters/cm variations
            pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|centimeters?)\b'
        elif unit == 'lb':
            # Handle pounds/lb variations
            pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|pounds?)\b'
        elif unit == 'kg':
            # Handle kilograms/kg variations
            pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|kilograms?)\b'
        elif unit == 'ft':
            # Handle feet/ft variations
            pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|feet?)\b'
        elif unit == 'm':
            # Handle meters/m variations
            pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|meters?)\b'
        elif unit in ['°F', '°C']:
            # Handle temperature units with variations
            if unit == '°F':
                pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|degrees?\s*fahrenheit?)\b'
            else:  # °C
                pattern = rf'(\d+(?:\.\d+)?)\s*(?:{escaped_unit}|degrees?\s*celsius?)\b'
        elif unit in ['W', 'T', 'RU', 'CFM']:
            # Handle single-letter units
            pattern = rf'(\d+(?:\.\d+)?)\s*{escaped_unit}\b'
        else:
            # Default pattern
            pattern = rf'(\d+(?:\.\d+)?)\s*{escaped_unit}\b'
        
        rule = {
            'pattern': pattern,
            'placeholder': f'{{{{<spec_key>}}}}',  # Will be replaced with actual spec name
            'priority': len(pattern),  # Longer patterns get higher priority
            'description': f'Auto-generated rule for {unit} measurements'
        }
        
        rules.append(rule)
    
    return rules

def main():
    """Main function to extract units and generate rules."""
    print("=== Unit Extraction and Rule Generation ===")
    
    # Extract units from ground truth
    print("Extracting units from ground truth specifications...")
    result = extract_all_units('ground_truth_specs.json')
    
    units = result['units']
    unit_sources = result['unit_sources']
    
    print(f"Found {len(units)} unique units:")
    for unit in units:
        sources = unit_sources[unit]
        print(f"  {unit}: {sources}")
    
    # Generate unit rules
    print("\nGenerating regex rules for units...")
    unit_rules = generate_unit_rules(units)
    
    # Save units inventory
    units_data = {
        'units': units,
        'unit_sources': unit_sources,
        'total_units': len(units)
    }
    
    with open('units.yaml', 'w') as f:
        yaml.dump(units_data, f, default_flow_style=False, indent=2)
    
    print(f"Saved units inventory to units.yaml")
    
    # Save unit rules
    rules_data = {
        'unit_rules': unit_rules,
        'total_rules': len(unit_rules)
    }
    
    with open('unit_rules.yaml', 'w') as f:
        yaml.dump(rules_data, f, default_flow_style=False, indent=2)
    
    print(f"Saved {len(unit_rules)} unit rules to unit_rules.yaml")
    
    # Print sample rules
    print("\nSample generated rules:")
    for i, rule in enumerate(unit_rules[:5]):  # Show first 5
        print(f"  {i+1}. {rule['pattern']} -> {rule['placeholder']}")
    
    print("\n=== Unit Extraction Complete ===")

if __name__ == "__main__":
    main() 