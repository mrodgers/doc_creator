#!/usr/bin/env python3
"""
Analyze Cisco Acronyms PDF for integration into the AI Document Generation System.
"""

import json
import re
from pathlib import Path
import PyPDF2


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def analyze_acronyms_structure(text: str) -> dict:
    """Analyze the structure of the acronyms document."""
    lines = text.split('\n')
    
    # Look for patterns in the document
    acronym_patterns = []
    section_patterns = []
    current_section = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Look for section headers (usually in caps or with numbers)
        if re.match(r'^[A-Z\s]+$', line) and len(line) > 3:
            section_patterns.append({
                'line_number': i,
                'text': line,
                'type': 'section_header'
            })
            current_section = line
            
        # Look for acronym patterns (typically "ACRONYM - Definition")
        acronym_match = re.match(r'^([A-Z0-9]+)\s*[-–—]\s*(.+)$', line)
        if acronym_match:
            acronym_patterns.append({
                'line_number': i,
                'acronym': acronym_match.group(1),
                'definition': acronym_match.group(2).strip(),
                'section': current_section,
                'full_line': line
            })
            
        # Look for multi-line acronym definitions
        elif re.match(r'^[A-Z0-9]{2,}$', line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not re.match(r'^[A-Z\s]+$', next_line):
                acronym_patterns.append({
                    'line_number': i,
                    'acronym': line,
                    'definition': next_line,
                    'section': current_section,
                    'full_line': f"{line} - {next_line}"
                })
    
    return {
        'total_lines': len(lines),
        'sections': section_patterns,
        'acronyms': acronym_patterns,
        'sample_lines': lines[:20]  # First 20 lines for context
    }


def extract_acronyms_dict(text: str) -> dict:
    """Extract acronyms into a dictionary format."""
    lines = text.split('\n')
    acronyms = {}
    current_section = "General"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers
        if re.match(r'^[A-Z\s]+$', line) and len(line) > 3:
            current_section = line
            continue
            
        # Extract acronym and definition
        acronym_match = re.match(r'^([A-Z0-9]+)\s*[-–—]\s*(.+)$', line)
        if acronym_match:
            acronym = acronym_match.group(1)
            definition = acronym_match.group(2).strip()
            acronyms[acronym] = {
                'definition': definition,
                'section': current_section
            }
            
        # Handle multi-line definitions
        elif re.match(r'^[A-Z0-9]{2,}$', line):
            acronym = line
            # Look ahead for definition
            for i in range(1, 4):  # Check next few lines
                if len(lines) > i:
                    next_line = lines[i].strip()
                    if next_line and not re.match(r'^[A-Z\s]+$', next_line):
                        acronyms[acronym] = {
                            'definition': next_line,
                            'section': current_section
                        }
                        break
    
    return acronyms


def main():
    """Main analysis function."""
    pdf_path = "cisco_acronyms.pdf"
    
    print("🔍 Analyzing Cisco Acronyms PDF...")
    print("=" * 50)
    
    # Extract text from PDF
    print("📄 Extracting text from PDF...")
    text = extract_pdf_text(pdf_path)
    
    if not text:
        print("❌ Failed to extract text from PDF")
        return
    
    print(f"✅ Extracted {len(text)} characters of text")
    
    # Analyze structure
    print("\n📊 Analyzing document structure...")
    structure = analyze_acronyms_structure(text)
    
    print(f"📈 Structure Analysis:")
    print(f"   Total lines: {structure['total_lines']}")
    print(f"   Sections found: {len(structure['sections'])}")
    print(f"   Acronyms found: {len(structure['acronyms'])}")
    
    # Show sample sections
    print(f"\n📋 Sample Sections:")
    for section in structure['sections'][:5]:
        print(f"   - {section['text']}")
    
    # Show sample acronyms
    print(f"\n🔤 Sample Acronyms:")
    for acronym in structure['acronyms'][:10]:
        print(f"   {acronym['acronym']}: {acronym['definition'][:50]}...")
    
    # Extract full acronym dictionary
    print(f"\n📚 Extracting full acronym dictionary...")
    acronyms_dict = extract_acronyms_dict(text)
    
    print(f"✅ Extracted {len(acronyms_dict)} acronyms")
    
    # Save to JSON for integration
    output_file = "cisco_acronyms_extracted.json"
    with open(output_file, 'w') as f:
        json.dump(acronyms_dict, f, indent=2)
    
    print(f"💾 Saved to {output_file}")
    
    # Integration recommendations
    print(f"\n🔧 Integration Recommendations:")
    print(f"1. **Acronym Expansion**: Use acronyms to expand section titles")
    print(f"2. **Synonym Generation**: Include acronyms in synonym lists")
    print(f"3. **Matching Enhancement**: Match acronyms to full terms")
    print(f"4. **Cache Integration**: Cache acronym lookups for performance")
    print(f"5. **Section Categorization**: Use acronym sections for better organization")
    
    # Show statistics
    sections = set(acronym['section'] for acronym in structure['acronyms'])
    print(f"\n📊 Statistics:")
    print(f"   Unique sections: {len(sections)}")
    print(f"   Average acronyms per section: {len(structure['acronyms']) / len(sections):.1f}")
    
    return acronyms_dict


if __name__ == "__main__":
    main() 