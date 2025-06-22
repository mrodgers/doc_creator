# quality_validation.py
"""
Automated Quality Validation for Spec Extraction

Compares the extracted specifications against a ground-truth dataset and reports coverage
and accuracy metrics.

Usage:
    python quality_validation.py \
        --extracted extracted_specs.json \
        --ground truth_specs.json

Inputs:
    --extracted: Path to the JSON output from the extraction step (extracted_specs.json)
    --ground:    Path to a JSON file with the ground-truth specs in the same format

Output:
    Prints a summary of:
      - Total specs in ground truth
      - Total extracted specs
      - Number of matched spec items
      - List of missing spec items
      - List of extra spec items
      - Coverage (%) = matched / total ground
      - Accuracy (%) = exact value matches / matched

Best Practices:
  - Uses plain JSON for interoperability
  - Simple CLI interface for integration
  - Reports clear metrics to guide iterative improvement
"""

import json
import argparse


def load_specs(path):
    """
    Load specs from a JSON file as a dict of spec_item -> value.
    """
    with open(path, 'r') as f:
        data = json.load(f)
    # Expecting a list of {"spec_item": ..., "value": ...}
    specs = {}
    for entry in data:
        key = entry.get('spec_item')
        val = entry.get('value')
        if key is not None:
            specs[key] = val
    return specs


def main():
    parser = argparse.ArgumentParser(description='Validate spec extraction quality')
    parser.add_argument('--extracted', required=True, help='Path to extracted_specs.json')
    parser.add_argument('--ground', required=True, help='Path to ground_truth_specs.json')
    args = parser.parse_args()

    extracted = load_specs(args.extracted)
    ground = load_specs(args.ground)

    extracted_items = set(extracted.keys())
    ground_items = set(ground.keys())

    matched_items = extracted_items & ground_items
    missing_items = ground_items - extracted_items
    extra_items = extracted_items - ground_items

    total_ground = len(ground_items)
    total_extracted = len(extracted_items)
    matched_count = len(matched_items)

    coverage = (matched_count / total_ground * 100) if total_ground else 0.0
    accuracy = (
        sum(1 for k in matched_items if extracted[k] == ground[k]) / matched_count * 100
    ) if matched_count else 0.0

    print("=== Quality Validation Report ===")
    print(f"Total ground-truth specs : {total_ground}")
    print(f"Total extracted specs   : {total_extracted}")
    print(f"Matched specs           : {matched_count}")
    print(f"Missing specs           : {len(missing_items)} -> {sorted(missing_items)}")
    print(f"Extra specs             : {len(extra_items)} -> {sorted(extra_items)}")
    print(f"Coverage                : {coverage:.2f}%")
    print(f"Accuracy (value match)  : {accuracy:.2f}%")
    print("=================================")


if __name__ == '__main__':
    main()
