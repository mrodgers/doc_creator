# extract_chapter1.py
"""
This script extracts Chapter 1 (Overview) from the Nexus 9364C ACI Mode Hardware Install Guide PDF,
splits it into structured sections, and writes out chapter1_overview.json with non-empty content.

Requirements:
    pip install pdfplumber
"""

import json
import re
import pdfplumber
import argparse

def extract_chapter(
    pdf_path: str,
    out_json: str = "chapter1_overview.json",
    chapter_start: str = "CHAPTER 1",
    chapter_end: str = "CHAPTER 2"
):
    data = {"title": "Chapter 1: Overview", "sections": []}
    pages_text = []

    # Open PDF and collect text between start/end markers
    with pdfplumber.open(pdf_path) as pdf:
        capture = False
        for page in pdf.pages:
            text = page.extract_text() or ""
            
            # Look for the actual start of Chapter 1 content (the specific sentence about the switch)
            if "Cisco Nexus 9364C-H1 switch" in text or "N9K-C9364C-H1" in text:
                capture = True
                print(f"Found Chapter 1 content on page with text length: {len(text)}")
            
            if capture:
                pages_text.append(text)
            
            # Stop at Chapter 2
            if chapter_end in text and capture:
                break

    full_text = "\n".join(pages_text).strip()
    if not full_text:
        raise RuntimeError("No text captured for Chapter 1—check your start/end markers.")

    print(f"Captured text length: {len(full_text)}")
    print(f"First 500 chars: {full_text[:500]}")

    # Split into subsections based on patterns like "1.1 Section Title"
    pattern = re.compile(r"^(\d+\.\d+)\s+([^\n]+)", re.MULTILINE)
    matches = list(pattern.finditer(full_text))
    sections = []

    # If no matches, treat entire chapter as one section
    if not matches:
        data["sections"].append({
            "heading": "Overview",
            "level": 1,
            "content": full_text.splitlines()
        })
    else:
        for idx, match in enumerate(matches):
            heading_num = match.group(1)
            heading_text = match.group(2).strip()
            start = match.end()
            end = matches[idx+1].start() if idx+1 < len(matches) else len(full_text)
            section_body = full_text[start:end].strip().splitlines()
            sections.append({
                "heading": f"{heading_num} {heading_text}",
                "level": 2,
                "content": section_body
            })
        data["sections"] = sections

    # Save to JSON
    with open(out_json, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Extracted {len(data['sections'])} sections to {out_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract Chapter 1 from PDF')
    parser.add_argument('--pdf', default="cisco-nexus-9364c_h1_aci_mode_hardware_install_guide.pdf",
                        help='Path to the PDF file')
    args = parser.parse_args()
    
    extract_chapter(args.pdf)