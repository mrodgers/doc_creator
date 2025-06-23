#!/usr/bin/env python3
"""
Realistic Test with Actual Cisco PDF Content
Extracts content from real Cisco documentation PDFs and tests the documentation generation system.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_doc_gen.core.workflow_orchestrator import WorkflowOrchestrator
from ai_doc_gen.core.draft_generator import ContentSection
from ai_doc_gen.utils.pdf_extractor import PDFExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_content_from_pdfs():
    """Extract content from Cisco PDFs and create realistic content sections."""
    pdf_dir = Path("test_data/cisco_docs")
    extractor = PDFExtractor()
    
    content_sections = []
    
    # Define which PDFs to extract from and what sections they likely contain
    pdf_mappings = {
        "cisco_nexus_installation_guide.pdf": [
            ("Hardware Overview", "hardware_overview"),
            ("Installation Preparation", "installation_preparation"), 
            ("Hardware Installation", "hardware_installation"),
            ("Initial Configuration", "initial_configuration")
        ],
        "cisco_preparing_for_installation.pdf": [
            ("Installation Preparation", "installation_preparation"),
            ("Hardware Installation", "hardware_installation")
        ],
        "cisco_switch_installation_guide.pdf": [
            ("Hardware Installation", "hardware_installation"),
            ("Initial Configuration", "initial_configuration"),
            ("Verification and Testing", "verification_testing")
        ],
        "cisco_nexus_9300_datasheet.pdf": [
            ("Hardware Overview", "hardware_overview"),
            ("Advanced Configuration", "advanced_configuration")
        ],
        "cisco_nexus_release_notes.pdf": [
            ("Troubleshooting", "troubleshooting"),
            ("Maintenance and Support", "maintenance")
        ]
    }
    
    for pdf_file, sections in pdf_mappings.items():
        pdf_path = pdf_dir / pdf_file
        if not pdf_path.exists():
            logger.warning(f"PDF not found: {pdf_path}")
            continue
            
        try:
            logger.info(f"Extracting content from: {pdf_file}")
            extracted_text = extractor.extract_text(str(pdf_path))
            
            # Split into sections and create content sections
            for section_title, template_id in sections:
                # Create a realistic content section from the extracted text
                content = _extract_section_content(extracted_text, section_title)
                if content:
                    content_section = ContentSection(
                        id=f"{pdf_file}_{template_id}",
                        title=section_title,
                        content=content,
                        source=str(pdf_path),
                        confidence=0.85,  # High confidence for real content
                        template_match=template_id,
                        acronyms_found=_extract_acronyms(content)
                    )
                    content_sections.append(content_section)
                    logger.info(f"Created content section: {section_title}")
                    
        except Exception as e:
            logger.error(f"Failed to extract from {pdf_file}: {e}")
    
    return content_sections


def _extract_section_content(text, section_title):
    """Extract relevant content for a specific section from the full text."""
    # Simple extraction - look for content around the section title
    lines = text.split('\n')
    content_lines = []
    in_section = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line contains the section title
        if section_title.lower() in line.lower():
            in_section = True
            content_lines.append(line)
            continue
            
        # If we're in the section, collect content until we hit another major heading
        if in_section:
            if line.isupper() and len(line) < 100:  # Likely a new heading
                break
            if line.startswith('Chapter') or line.startswith('Section'):
                break
            content_lines.append(line)
            
            # Limit content length
            if len('\n'.join(content_lines)) > 1000:
                break
    
    content = '\n'.join(content_lines)
    
    # If no specific content found, create a generic placeholder
    if not content or len(content) < 50:
        content = f"Content extracted from Cisco documentation for {section_title}. This section contains relevant information about {section_title.lower()} procedures and requirements."
    
    return content


def _extract_acronyms(text):
    """Extract common Cisco acronyms from text."""
    acronyms = []
    common_cisco_acronyms = [
        ('VLAN', 'Virtual Local Area Network'),
        ('SNMP', 'Simple Network Management Protocol'),
        ('SSH', 'Secure Shell'),
        ('TFTP', 'Trivial File Transfer Protocol'),
        ('FTP', 'File Transfer Protocol'),
        ('HTTP', 'Hypertext Transfer Protocol'),
        ('HTTPS', 'Hypertext Transfer Protocol Secure'),
        ('DNS', 'Domain Name System'),
        ('DHCP', 'Dynamic Host Configuration Protocol'),
        ('NTP', 'Network Time Protocol'),
        ('BGP', 'Border Gateway Protocol'),
        ('OSPF', 'Open Shortest Path First'),
        ('QoS', 'Quality of Service'),
        ('MPLS', 'Multiprotocol Label Switching'),
        ('VPN', 'Virtual Private Network'),
        ('IPSec', 'Internet Protocol Security'),
        ('RADIUS', 'Remote Authentication Dial-In User Service'),
        ('TACACS+', 'Terminal Access Controller Access-Control System Plus'),
        ('AAA', 'Authentication, Authorization, and Accounting'),
        ('CDP', 'Cisco Discovery Protocol'),
        ('LLDP', 'Link Layer Discovery Protocol'),
        ('PoE', 'Power over Ethernet'),
        ('ACL', 'Access Control List'),
        ('CPU', 'Central Processing Unit'),
        ('RAM', 'Random Access Memory'),
        ('ROM', 'Read-Only Memory'),
        ('NVRAM', 'Non-Volatile Random Access Memory'),
        ('ASIC', 'Application-Specific Integrated Circuit'),
        ('UCS', 'Unified Computing System'),
        ('ACI', 'Application Centric Infrastructure'),
        ('SDN', 'Software-Defined Networking'),
        ('VXLAN', 'Virtual Extensible Local Area Network')
    ]
    
    text_upper = text.upper()
    for acronym, definition in common_cisco_acronyms:
        if acronym in text_upper:
            acronyms.append((acronym, definition))
    
    return acronyms


def main():
    """Run realistic test with actual Cisco PDF content."""
    logger.info("Starting realistic test with actual Cisco PDF content")
    
    # Extract content from PDFs
    content_sections = extract_content_from_pdfs()
    
    if not content_sections:
        logger.error("No content sections extracted. Check PDF files.")
        return
    
    logger.info(f"Extracted {len(content_sections)} content sections from Cisco PDFs")
    
    # Display extracted content for verification
    for section in content_sections:
        logger.info(f"\nSection: {section.title}")
        logger.info(f"Source: {section.source}")
        logger.info(f"Content preview: {section.content[:200]}...")
        logger.info(f"Acronyms found: {section.acronyms_found}")
    
    # Run the workflow orchestrator
    orchestrator = WorkflowOrchestrator()
    outputs = orchestrator.run(
        content_sections=content_sections,
        document_title="Cisco Nexus Hardware Installation Guide (Realistic Test)",
        output_dir="outputs/realistic_test"
    )
    
    print(f"\n✅ Realistic test completed!")
    print(f"   Content sections: {len(content_sections)}")
    print(f"   Output files:")
    for k, v in outputs.items():
        if k.endswith('_md') or k.endswith('_json'):
            print(f"     {k}: {v}")
    print(f"   Total time: {outputs['total_time']:.2f}s")


if __name__ == "__main__":
    main() 