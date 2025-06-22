# extract_specs.py
"""
This script reads the structured Chapter 1 JSON, calls GPT-4o via the OpenAI API
to extract spec items and their values, and writes the output to extracted_specs.json.

Requirements:
    pip install openai
    export OPENAI_API_KEY="your_api_key_here"
"""

import os
import json
import openai
import re

def load_chapter_json(path):
    with open(path, "r") as f:
        return json.load(f)

def extract_specs(chapter_json):
    # Build the prompt messages
    system_message = {
        "role": "system",
        "content": (
            "You are a technical document parser specialized in extracting hardware specifications. "
            "You must extract EXACTLY the following 31 fields from the provided Chapter 1 content. "
            "If a field is not found in the text, return its value as an empty string. "
            "For each field, also provide a confidence score from 0-100 indicating how sure you are that this value was correctly identified. "
            "Always return a JSON array with exactly 31 objects, one for each field."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            "Please extract the following fields (exactly these names), in JSON form with spec_item / value / confidence:\n"
            "• Product name\n"
            "• Model number\n"
            "• Rack units\n"
            "• Traffic processing capability\n"
            "• QSFP port count\n"
            "• Management ports\n"
            "• Console port\n"
            "• USB port\n"
            "• Fan modules\n"
            "• Port-side exhaust fan module part number\n"
            "• Port-side intake fan module part number\n"
            "• Power supply modules\n"
            "• 1400-W AC power supply part number\n"
            "• 1400-W AC power supply part number (intake)\n"
            "• 2000-W HVAC/HVDC power supply part number\n"
            "• 2000-W DC power supply part number\n"
            "• 2000-W DC power supply part number (intake)\n"
            "• Chassis width\n"
            "• Chassis depth\n"
            "• Chassis height\n"
            "• Chassis weight\n"
            "• Fan module weight\n"
            "• Power supply module weight\n"
            "• Power input requirements\n"
            "• Heat dissipation\n"
            "• Operating temperature\n"
            "• Non-operating temperature\n"
            "• Altitude rating\n"
            "• Humidity requirements\n"
            "• Power supply redundancy\n"
            "• Regulatory compliance\n\n"
            "Example input:\n"
            "Chapter excerpt: \"The Cisco Nexus 9364C-H1 switch (N9K-C9364C-H1) is a 2-rack unit (RU), fixed-port switch designed for spine-leaf-APIC deployment in data centers. The software on this switch has 6.4T traffic-processing capability.\"\n\n"
            "Expected output:\n"
            "[\n"
            "  {\"spec_item\": \"Product name\", \"value\": \"Cisco Nexus 9364C-H1 switch\", \"confidence\": 95},\n"
            "  {\"spec_item\": \"Model number\", \"value\": \"N9K-C9364C-H1\", \"confidence\": 98},\n"
            "  {\"spec_item\": \"Rack units\", \"value\": \"2 RU\", \"confidence\": 92},\n"
            "  {\"spec_item\": \"Traffic processing capability\", \"value\": \"6.4T\", \"confidence\": 90},\n"
            "  {\"spec_item\": \"QSFP port count\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Management ports\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Console port\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"USB port\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Fan modules\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Port-side exhaust fan module part number\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Port-side intake fan module part number\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Power supply modules\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"1400-W AC power supply part number\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"1400-W AC power supply part number (intake)\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"2000-W HVAC/HVDC power supply part number\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"2000-W DC power supply part number\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"2000-W DC power supply part number (intake)\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Chassis width\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Chassis depth\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Chassis height\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Chassis weight\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Fan module weight\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Power supply module weight\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Power input requirements\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Heat dissipation\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Operating temperature\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Non-operating temperature\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Altitude rating\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Humidity requirements\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Power supply redundancy\", \"value\": \"\", \"confidence\": 100},\n"
            "  {\"spec_item\": \"Regulatory compliance\", \"value\": \"\", \"confidence\": 100}\n"
            "]\n\n"
            "Confidence scoring guidelines:\n"
            "- 90-100: Very confident, clear and unambiguous information\n"
            "- 70-89: Confident, but some ambiguity or interpretation required\n"
            "- 50-69: Somewhat confident, information may be incomplete or unclear\n"
            "- 30-49: Low confidence, significant ambiguity or missing context\n"
            "- 0-29: Very low confidence, highly uncertain or conflicting information\n"
            "- 100: Field not found in text (empty value)\n\n"
            "Here is the JSON for Chapter 1 – Overview:\n\n"
            f"{json.dumps(chapter_json, indent=2)}\n\n"
            "Please extract all 31 fields exactly as specified above with confidence scores."
        )
    }

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_message, user_message],
        temperature=0.0,
        max_tokens=4000  # Ensure enough tokens for confidence scores
    )

    return response.choices[0].message.content

def save_extracted_specs(output_str, output_path, threshold=90):
    print(f"Raw GPT output: {output_str[:200]}...")  # Debug output
    
    try:
        # First try to parse as-is
        specs = json.loads(output_str)
    except json.JSONDecodeError as e:
        print(f"Initial JSON parse failed: {e}")
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', output_str, re.DOTALL)
            if json_match:
                specs = json.loads(json_match.group(1))
            else:
                # Try to find JSON array or object in the text
                json_match = re.search(r'\[.*\]|\{.*\}', output_str, re.DOTALL)
                if json_match:
                    specs = json.loads(json_match.group(0))
                else:
                    # Last resort: try to wrap in array brackets
                    cleaned = output_str.strip().rstrip(',')
                    if not cleaned.startswith('['):
                        cleaned = f"[{cleaned}]"
                    specs = json.loads(cleaned)
        except json.JSONDecodeError as e2:
            print(f"All JSON parsing attempts failed: {e2}")
            # Save the raw output for debugging
            with open(output_path + ".debug", "w") as f:
                f.write(output_str)
            raise RuntimeError(f"Could not parse GPT output as JSON. Raw output saved to {output_path}.debug")
    
    # Add confidence scores if missing (backward compatibility)
    for entry in specs:
        if 'confidence' not in entry:
            entry['confidence'] = 100  # Fallback for backward compatibility
            print(f"Warning: No confidence score for {entry.get('spec_item', 'unknown')}, defaulting to 100")
    
    # Apply threshold-based triage
    auto_approved = [e for e in specs if e['confidence'] >= threshold]
    review_needed = [e for e in specs if e['confidence'] < threshold]
    
    # Save the full results with confidence scores
    with open(output_path, "w") as f:
        json.dump(specs, f, indent=2)
    
    # Save triage results
    triage_results = {
        "threshold": threshold,
        "total_specs": len(specs),
        "auto_approved": len(auto_approved),
        "review_needed": len(review_needed),
        "approved": auto_approved,
        "review": review_needed
    }
    
    triage_path = output_path.replace('.json', '_triage.json')
    with open(triage_path, "w") as f:
        json.dump(triage_results, f, indent=2)
    
    # Print summary
    print(f"\n=== Confidence Triage Summary ===")
    print(f"Threshold: {threshold}%")
    print(f"Total specs: {len(specs)}")
    print(f"Auto-approved: {len(auto_approved)} ({len(auto_approved)/len(specs)*100:.1f}%)")
    print(f"Review needed: {len(review_needed)} ({len(review_needed)/len(specs)*100:.1f}%)")
    
    if review_needed:
        print(f"\nSpecs requiring review:")
        for spec in review_needed:
            print(f"  - {spec['spec_item']}: {spec['value']} (confidence: {spec['confidence']}%)")
    
    # Calculate average confidence
    avg_confidence = sum(e['confidence'] for e in specs) / len(specs)
    print(f"\nAverage confidence: {avg_confidence:.1f}%")
    
    return specs, triage_results

def main():
    # Paths
    chapter_json_path = "chapter1_overview.json"
    output_path = "extracted_specs.json"

    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please set the OPENAI_API_KEY environment variable")

    # Load structured JSON
    chapter_json = load_chapter_json(chapter_json_path)

    # Extract specs via GPT-4o-mini
    print("Calling GPT-4o-mini to extract spec items with confidence scores...")
    output_str = extract_specs(chapter_json)
    print("Extraction complete. Saving results...")

    # Save results with confidence triage
    specs, triage_results = save_extracted_specs(output_str, output_path)
    print(f"Extracted specs written to {output_path}")
    print(f"Triage results written to {output_path.replace('.json', '_triage.json')}")
    
    return specs, triage_results

if __name__ == "__main__":
    main()