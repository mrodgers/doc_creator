#!/usr/bin/env python3
"""
Input Processing Example

Demonstrates the input processing functionality including document parsing,
structured extraction, and validation.
"""

import sys
import os
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_doc_gen.input_processing import (
    parse_document,
    extract_structured_content,
    validate_document
)
from ai_doc_gen.input_processing.document_parser import DocumentParserFactory
from ai_doc_gen.input_processing.structured_extractor import StructuredExtractor
from ai_doc_gen.input_processing.input_validator import InputValidator


def create_sample_documents():
    """Create sample documents for testing."""
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)
    
    # Create a sample text file
    sample_text = """
# Cisco Router Installation Guide

## Technical Specifications

The Cisco Router Model XYZ-1000 has the following specifications:
- Dimensions: 300mm x 200mm x 50mm
- Weight: 2.5kg
- Power: 100-240V AC, 50-60Hz
- Memory: 1GB RAM, 4GB Flash
- Ports: 4x Gigabit Ethernet, 1x Console, 1x USB

## Installation Requirements

Before installing the router, ensure you have:
- Minimum 2U rack space
- Power outlet (100-240V AC)
- Network cables (Cat5e or better)
- Console cable for initial configuration

## Installation Procedure

### Step 1: Physical Installation
1. Mount the router in a 19-inch rack using the provided mounting brackets
2. Ensure proper ventilation (minimum 2 inches clearance on all sides)
3. Connect the power cable to the router and power outlet

### Step 2: Network Connections
1. Connect network cables to the appropriate Ethernet ports
2. Connect the console cable to your computer for initial setup
3. Power on the router

### Step 3: Initial Configuration
1. Open a terminal emulator on your computer
2. Set the connection to 9600 baud, 8 data bits, no parity, 1 stop bit
3. Press Enter to access the router console

## Warnings and Notes

WARNING: Do not connect power while the router is open or being serviced.
WARNING: Ensure proper grounding to prevent electrical damage.

Note: The router may take up to 5 minutes to fully boot after power-on.
Note: Keep the original packaging for warranty purposes.

## Troubleshooting

### Common Issues
- Router won't power on: Check power cable and outlet
- No network connectivity: Verify cable connections and network settings
- Console access issues: Check terminal emulator settings

### Error Messages
- "Boot failed": Contact technical support
- "Memory error": Check memory module installation
"""
    
    # Write sample text file
    with open(samples_dir / "sample_installation_guide.txt", "w") as f:
        f.write(sample_text)
    
    print(f"Created sample document: {samples_dir / 'sample_installation_guide.txt'}")
    
    return samples_dir


def demonstrate_parser_factory():
    """Demonstrate the document parser factory."""
    print("\n" + "="*60)
    print("DOCUMENT PARSER FACTORY DEMONSTRATION")
    print("="*60)
    
    factory = DocumentParserFactory()
    supported_formats = factory.get_supported_formats()
    
    print(f"Supported document formats: {', '.join(supported_formats)}")
    
    # Test with different file types
    test_files = [
        "document.pdf",
        "document.docx", 
        "document.xml",
        "document.txt"
    ]
    
    for test_file in test_files:
        parser = factory.get_parser(test_file)
        if parser:
            print(f"✓ {test_file}: {parser.__class__.__name__}")
        else:
            print(f"✗ {test_file}: No parser available")


def demonstrate_validation():
    """Demonstrate input validation."""
    print("\n" + "="*60)
    print("INPUT VALIDATION DEMONSTRATION")
    print("="*60)
    
    validator = InputValidator()
    
    # Test validation with sample file
    sample_file = "samples/sample_installation_guide.txt"
    
    if os.path.exists(sample_file):
        print(f"Validating: {sample_file}")
        result = validator.validate_document(sample_file)
        
        print(f"Valid: {result.is_valid}")
        print(f"Score: {result.score:.2f}")
        
        if result.issues:
            print("\nIssues found:")
            for issue in result.issues:
                print(f"  [{issue.level.value.upper()}] {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
    else:
        print(f"Sample file not found: {sample_file}")


def demonstrate_structured_extraction():
    """Demonstrate structured content extraction."""
    print("\n" + "="*60)
    print("STRUCTURED CONTENT EXTRACTION DEMONSTRATION")
    print("="*60)
    
    sample_file = "samples/sample_installation_guide.txt"
    
    if not os.path.exists(sample_file):
        print(f"Sample file not found: {sample_file}")
        return
    
    # Parse the document
    try:
        parsed_doc = parse_document(sample_file)
        print(f"Parsed document: {parsed_doc.filename}")
        print(f"File type: {parsed_doc.file_type}")
        print(f"Title: {parsed_doc.title}")
        print(f"Sections: {len(parsed_doc.sections)}")
        print(f"Text length: {len(parsed_doc.raw_text)} characters")
        
        # Extract structured content
        extractor = StructuredExtractor()
        extracted_content = extractor.extract_structured_content(parsed_doc)
        
        print(f"\nExtracted {len(extracted_content)} content items:")
        
        for i, item in enumerate(extracted_content[:5], 1):  # Show first 5 items
            print(f"\n{i}. {item.title}")
            print(f"   Type: {item.content_type.value}")
            print(f"   Confidence: {item.confidence:.2f}")
            print(f"   Source: {item.source_section}")
            print(f"   Tags: {', '.join(item.tags) if item.tags else 'None'}")
            print(f"   Content: {item.content[:100]}{'...' if len(item.content) > 100 else ''}")
        
        # Generate summary
        summary = extractor.get_content_summary(extracted_content)
        print(f"\nContent Summary:")
        print(f"  Total items: {summary['total_items']}")
        print(f"  Content types: {summary['content_types']}")
        print(f"  Confidence distribution: {summary['confidence_distribution']}")
        print(f"  Top tags: {dict(list(summary['top_tags'].items())[:5])}")
        
    except Exception as e:
        print(f"Error processing document: {e}")


def demonstrate_end_to_end_processing():
    """Demonstrate end-to-end processing workflow."""
    print("\n" + "="*60)
    print("END-TO-END PROCESSING DEMONSTRATION")
    print("="*60)
    
    sample_file = "samples/sample_installation_guide.txt"
    
    if not os.path.exists(sample_file):
        print(f"Sample file not found: {sample_file}")
        return
    
    try:
        # Step 1: Validate the document
        print("Step 1: Validating document...")
        validation_result = validate_document(sample_file)
        
        if not validation_result.is_valid:
            print("Document validation failed!")
            for warning in validation_result.warnings:
                print(f"  Warning: {warning}")
            return
        
        print(f"✓ Document validated (score: {validation_result.score:.2f})")
        
        # Step 2: Parse the document
        print("\nStep 2: Parsing document...")
        parsed_doc = parse_document(sample_file)
        print(f"✓ Document parsed ({len(parsed_doc.sections)} sections)")
        
        # Step 3: Extract structured content
        print("\nStep 3: Extracting structured content...")
        extracted_content = extract_structured_content(parsed_doc)
        print(f"✓ Content extracted ({len(extracted_content)} items)")
        
        # Step 4: Generate report
        print("\nStep 4: Generating processing report...")
        
        report = {
            "document_info": {
                "filename": parsed_doc.filename,
                "file_type": parsed_doc.file_type,
                "title": parsed_doc.title,
                "sections": len(parsed_doc.sections),
                "text_length": len(parsed_doc.raw_text)
            },
            "validation": {
                "is_valid": validation_result.is_valid,
                "score": validation_result.score,
                "issues_count": len(validation_result.issues)
            },
            "extraction": {
                "total_items": len(extracted_content),
                "content_types": {},
                "high_confidence_items": 0
            }
        }
        
        # Count content types
        for item in extracted_content:
            content_type = item.content_type.value
            report["extraction"]["content_types"][content_type] = \
                report["extraction"]["content_types"].get(content_type, 0) + 1
            
            if item.confidence >= 0.8:
                report["extraction"]["high_confidence_items"] += 1
        
        print("✓ Processing report generated:")
        print(json.dumps(report, indent=2))
        
        # Save report to file
        report_file = "processing_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_file}")
        
    except Exception as e:
        print(f"Error in end-to-end processing: {e}")


def main():
    """Main demonstration function."""
    print("AI DOCUMENTATION GENERATION - INPUT PROCESSING DEMONSTRATION")
    print("="*80)
    
    # Create sample documents
    print("Creating sample documents...")
    create_sample_documents()
    
    # Run demonstrations
    demonstrate_parser_factory()
    demonstrate_validation()
    demonstrate_structured_extraction()
    demonstrate_end_to_end_processing()
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the processing_report.json file")
    print("2. Try with your own documents")
    print("3. Explore the extracted content for AI processing")
    print("4. Check the validation results for document quality")


if __name__ == "__main__":
    main() 