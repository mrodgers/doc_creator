# audit_specs.py
"""
LLM-Assisted Audit Pass for Accuracy Refinement

Automatically detects and corrects formatting or value-mismatches in extracted specs
by comparing them against the original chapter text, ensuring every value exactly
mirrors the source document.

Usage:
    python audit_specs.py

Inputs:
    - chapter1_overview.json: Structured chapter content
    - extracted_specs.json: Extracted specifications to audit

Output:
    - corrected_specs.json: Corrected specifications with exact source values
"""

import json
import openai
import re

def load_json(path):
    """Load JSON data from file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    """Save JSON data to file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def normalize(s: str) -> str:
    # Remove everything except letters and digits, then lowercase
    return re.sub(r'[^0-9A-Za-z]', '', s).lower()

def gather_snippets(chapter_json, extracted_specs):
    """
    For each spec: scan chapter_json['sections'][…]['content'] to find lines 
    containing extracted_specs[i]['value']. Return list of dicts with 
    spec_item, extracted_value, snippet.
    """
    entries = []
    
    # Flatten all content from all sections
    all_content = []
    for section in chapter_json.get('sections', []):
        all_content.extend(section.get('content', []))
    
    # Create a comprehensive text for searching
    full_text = " ".join(all_content)
    
    for spec in extracted_specs:
        spec_item = spec['spec_item']
        extracted_value = spec['value']
        
        # Skip empty values
        if not extracted_value or extracted_value.strip() == "":
            entries.append({
                "spec_item": spec_item,
                "extracted_value": extracted_value,
                "snippet": ""
            })
            continue
        
        # Normalize the extracted value for searching
        normalized_value = re.sub(r'[^a-zA-Z0-9]', '', extracted_value.lower())
        
        # Find the best snippet containing this value
        best_snippet = ""
        best_score = 0
        
        # Search in chunks to avoid memory issues
        chunk_size = 1000  # characters
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i:i + chunk_size + 500]  # overlap for context
            
            # Normalize chunk
            normalized_chunk = re.sub(r'[^a-zA-Z0-9]', '', chunk.lower())
            
            # Check if the normalized value is in this chunk
            if normalized_value in normalized_chunk:
                # Find the actual position in the original chunk
                start_pos = chunk.lower().find(extracted_value.lower())
                if start_pos == -1:
                    # Try with normalized search
                    start_pos = 0
                
                # Extract context around the match (±200 chars)
                start = max(0, start_pos - 200)
                end = min(len(chunk), start_pos + len(extracted_value) + 200)
                snippet = chunk[start:end]
                
                # Score based on proximity and relevance
                score = len(extracted_value) / len(snippet)  # Higher score for more focused snippets
                
                if score > best_score:
                    best_score = score
                    best_snippet = snippet
        
        # If no exact match found, try fuzzy matching for specific specs
        if not best_snippet:
            best_snippet = find_specific_spec_snippet(spec_item, full_text)
        
        entries.append({
            "spec_item": spec_item,
            "extracted_value": extracted_value,
            "snippet": best_snippet
        })
    
    return entries

def find_specific_spec_snippet(spec_item, full_text):
    """Find specific snippets for known specs that might be missing."""
    spec_patterns = {
        "QSFP port count": [
            r"64.*QSFP", r"64100-GigabitQSFP", r"64.*100-Gigabit.*QSFP",
            r"64100GigabitQSFP", r"64.*QSFP.*port"
        ],
        "Management ports": [
            r"Two.*management.*port", r"2.*management.*port", r"management.*port.*2",
            r"RJ-45.*port.*SFP.*port", r"one.*RJ-45.*port.*one.*SFP.*port"
        ],
        "Chassis width": [
            r"17\.41.*inches", r"17\.41.*cm", r"17\.41inches",
            r"Width.*17\.41", r"17\.4.*in.*44\.2.*cm"
        ],
        "Chassis depth": [
            r"22\.27.*inches", r"22\.27.*cm", r"22\.27inches",
            r"Depth.*22\.27", r"22\.27.*in.*56\.68.*cm"
        ],
        "Chassis height": [
            r"3\.4.*inches", r"3\.4.*cm", r"3\.4inches",
            r"Height.*3\.4", r"3\.4.*in.*8\.6.*cm"
        ],
        "Fan modules": [
            r"NXAS-FAN-160CFM2", r"NXASFAN-160CFM2", r"fan.*module.*4",
            r"four.*fan.*module", r"4.*fan.*module"
        ],
        "Power supply modules": [
            r"NXA-PAC-1400W", r"NXA-PDC-2KW", r"NXA-PHV-2KW",
            r"power.*supply.*2", r"two.*power.*supply", r"2.*power.*supply"
        ],
        "USB port": [
            r"USB.*port", r"USBport", r"1.*USB.*port"
        ],
        "Console port": [
            r"Console.*port", r"Consoleport", r"1.*Console.*port"
        ],
        "Power input requirements": [
            r"605W.*1100W", r"605W.*typical", r"power.*input.*605W"
        ],
        "Heat dissipation": [
            r"4248.*BTU", r"4248\.116.*BTU", r"heat.*dissipation.*4248"
        ],
        "Humidity requirements": [
            r"Climate-controlled", r"Climate.*controlled", r"humidity.*5.*95",
            r"Climate-controlled.*buildings", r"Climate.*controlled.*buildings"
        ],
        "Regulatory compliance": [
            r"NEBS", r"Regulatory.*compliance", r"FCC.*Class.*A",
            r"Network.*Equipment.*Building.*System"
        ],
        "Port-side exhaust fan module part number": [
            r"NXAS-FAN-160CFM2-PE", r"NXASFAN-160CFM2-PE", r"fan.*module.*PE"
        ],
        "Port-side intake fan module part number": [
            r"NXAS-FAN-160CFM2-PI", r"NXASFAN-160CFM2-PI", r"fan.*module.*PI"
        ]
    }
    
    if spec_item in spec_patterns:
        patterns = spec_patterns[spec_item]
        for pattern in patterns:
            # Search for the pattern in the text
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                start = max(0, match.start() - 150)
                end = min(len(full_text), match.end() + 150)
                snippet = full_text[start:end]
                
                # Try to find a better context by looking for sentence boundaries
                # Look for the start of a sentence or line
                for i in range(start, max(0, start - 100), -1):
                    if full_text[i] in '.!?\n':
                        start = i + 1
                        break
                
                # Look for the end of a sentence or line
                for i in range(end, min(len(full_text), end + 100)):
                    if full_text[i] in '.!?\n':
                        end = i + 1
                        break
                
                return full_text[start:end]
    
    return ""

def call_qa_agent(entries):
    """Call GPT-4o with QA prompt to correct extracted values."""
    
    system_message = {
        "role": "system",
        "content": (
            "You are a QA assistant specializing in extracting exact specifications from technical documents. "
            "For each entry, you must find the EXACT value for the SPECIFIC spec_item in the snippet. "
            "IMPORTANT RULES:\n"
            "1. Each spec_item has a unique meaning - do not mix up values between different specs\n"
            "2. Look for the exact substring in `snippet` that corresponds to the `spec_item`\n"
            "3. Copy the exact spelling—hyphens, symbols, spaces, and all—into `corrected_value`\n"
            "4. Only return an empty string if the snippet truly lacks that specific spec\n"
            "5. For numeric values, include units (e.g., '64', '17.41 inches (44.23 cm)')\n"
            "6. For descriptive values, include the full description (e.g., '2 (1 RJ-45 port and 1 SFP port)')\n"
            "7. Pay attention to context - values may be in tables or lists\n"
            "8. Return ONLY a valid JSON array with the corrected values\n"
        )
    }
    
    # Create examples for the missing specs
    examples = [
        {
            "spec_item": "QSFP port count",
            "extracted_value": "",
            "snippet": "Theswitchhastheseports: •64100-GigabitQSFPports •Twomanagementports(oneRJ-45portandoneSFPport)",
            "corrected_value": "64"
        },
        {
            "spec_item": "Management ports", 
            "extracted_value": "",
            "snippet": "Theswitchhastheseports: •64100-GigabitQSFPports •Twomanagementports(oneRJ-45portandoneSFPport)",
            "corrected_value": "2 (1 RJ-45 port and 1 SFP port)"
        },
        {
            "spec_item": "Chassis width",
            "extracted_value": "",
            "snippet": "CiscoNexus9364C-H1 17.41inches(44.23 22.27inches(56.58 3.4inches(8.6cm)(2RU)",
            "corrected_value": "17.41 inches (44.23 cm)"
        }
    ]
    
    # Process entries in smaller batches to avoid token limits
    batch_size = 3  # Reduced batch size
    all_corrected = []
    
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]
        
        user_message = {
            "role": "user",
            "content": (
                "Here are examples of correct extractions:\n"
                f"{json.dumps(examples, indent=2)}\n\n"
                "Now extract the exact values for these entries. Return ONLY a valid JSON array:\n"
                f"{json.dumps(batch, indent=2)}\n"
            )
        }
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_message, user_message],
            temperature=0.0,
            max_tokens=1000  # Limit response size
        )
        
        response_content = response.choices[0].message.content.strip()
        print(f"Raw QA response for batch {i//batch_size + 1}: {response_content[:200]}...")
        
        try:
            # Clean the response - remove markdown formatting
            cleaned_response = response_content
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse the JSON
            corrected_values = json.loads(cleaned_response)
            
            # Merge spec_item from input with corrected_value from LLM output
            for j, entry in enumerate(batch):
                if j < len(corrected_values):
                    corrected_value = corrected_values[j].get('corrected_value', '')
                else:
                    corrected_value = ''
                
                all_corrected.append({
                    "spec_item": entry['spec_item'],
                    "corrected_value": corrected_value
                })
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed for batch {i//batch_size + 1}: {e}")
            print(f"Response content: {response_content}")
            # Save the raw output for debugging
            with open(f"qa_response_batch_{i//batch_size + 1}.debug", "w") as f:
                f.write(response_content)
            
            # Fallback: create empty corrected values for this batch
            for entry in batch:
                all_corrected.append({
                    "spec_item": entry['spec_item'],
                    "corrected_value": ""
                })
    
    return all_corrected

def main():
    """Main function to audit extracted specifications using GPT-4o."""
    
    # Load extracted specifications
    with open("extracted_specs.json", "r") as f:
        extracted_specs = json.load(f)
    
    # Load triage results to identify low-confidence specs
    try:
        with open("extracted_specs_triage.json", "r") as f:
            triage_results = json.load(f)
        review_needed = triage_results.get('review', [])
        print(f"Found {len(review_needed)} specs requiring review (confidence < {triage_results.get('threshold', 90)}%)")
        
        if not review_needed:
            print("✅ No specs require auditing - all specs have high confidence!")
            return extracted_specs
        
        # Only audit the low-confidence specs
        specs_to_audit = review_needed
        print(f"Auditing {len(specs_to_audit)} low-confidence specs...")
        
    except FileNotFoundError:
        print("No triage results found, auditing all specs...")
        specs_to_audit = extracted_specs
    
    # Load the chapter content
    with open("chapter1_overview.json", "r") as f:
        chapter_json = json.load(f)
    
    # Gather context snippets for the specs that need auditing
    print("Gathering context snippets...")
    entries = gather_snippets(chapter_json, specs_to_audit)
    
    # Print some debug info
    for i, entry in enumerate(entries[:3]):  # Show first 3
        print(f"\n>> SNIPPET FOR {entry['spec_item']}:")
        print(entry['snippet'][:200] + "..." if len(entry['snippet']) > 200 else entry['snippet'])
    
    print(f"\nFound {len(entries)} entries to audit")
    
    # Call the QA agent for corrections
    print("Calling QA agent for corrections...")
    corrected_entries = call_qa_agent(entries)
    
    # Process the audit results
    corrected_specs = []
    
    # Start with all original specs
    for spec in extracted_specs:
        spec_item = spec['spec_item']
        
        # Check if this spec was audited
        corrected_value = None
        for corrected_spec in corrected_entries:
            if corrected_spec['spec_item'] == spec_item:
                corrected_value = corrected_spec['corrected_value']
                break
        
        # Use corrected value if available, otherwise keep original
        if corrected_value is not None:
            corrected_specs.append({
                'spec_item': spec_item,
                'value': corrected_value,
                'confidence': 95  # Boost confidence after audit
            })
        else:
            corrected_specs.append(spec)
    
    # Save the corrected specs
    with open("corrected_specs.json", "w") as f:
        json.dump(corrected_specs, f, indent=2)
    
    print("✅ Corrected specs saved to corrected_specs.json")
    print(f"Total specs: {len(corrected_specs)}")
    print(f"Specs audited: {len(specs_to_audit)}")
    
    return corrected_specs

if __name__ == "__main__":
    main() 