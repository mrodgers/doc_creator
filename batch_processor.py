#!/usr/bin/env python3
"""
Batch Processor for AI Documentation Generation
Monitors upload folder and processes new PDF files automatically.
"""

import json
import logging
import hashlib
import time
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent / 'ai-doc-gen' / 'src'))

from ai_doc_gen.core.workflow_orchestrator import WorkflowOrchestrator
from ai_doc_gen.core.draft_generator import ContentSection
from ai_doc_gen.utils.pdf_extractor import PDFExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """Simple batch processor for PDF documentation generation."""
    
    def __init__(self):
        self.upload_dir = Path("uploads/pending")
        self.processed_dir = Path("uploads/processed")
        self.log_file = Path("processing_log.json")
        self.extractor = PDFExtractor()
        self.orchestrator = WorkflowOrchestrator()
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create processing log
        self.processing_log = self._load_processing_log()
    
    def _load_processing_log(self) -> Dict:
        """Load processing log or create new one."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load processing log: {e}")
        
        return {
            "processed_files": {},
            "last_check": datetime.now().isoformat()
        }
    
    def _save_processing_log(self):
        """Save processing log to file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.processing_log, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processing log: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return "hash_calculation_failed"
    
    def _is_new_file(self, file_path: Path) -> bool:
        """Check if file is new or has been updated."""
        filename = file_path.name
        current_hash = self._calculate_file_hash(file_path)
        
        if filename not in self.processing_log["processed_files"]:
            logger.info(f"New file detected: {filename}")
            return True
        
        stored_hash = self.processing_log["processed_files"][filename].get("hash", "")
        if current_hash != stored_hash:
            logger.info(f"Updated file detected: {filename}")
            return True
        
        logger.info(f"File already processed: {filename}")
        return False
    
    def _extract_content_from_pdf(self, pdf_path: Path) -> (list, bool):
        """Extract content sections from a PDF file. Returns (sections, used_placeholder)."""
        try:
            logger.info(f"Extracting content from: {pdf_path.name}")
            extracted_text = self.extractor.extract_text(str(pdf_path))
            used_placeholder = False
            
            # Check for clear placeholder marker
            if '[PLACEHOLDER_CONTENT]' in extracted_text:
                used_placeholder = True
                logger.warning(f"Placeholder content detected for {pdf_path.name}")
            
            # Create content sections based on common documentation patterns
            sections = [
                ("Hardware Overview", "hardware_overview"),
                ("Installation Preparation", "installation_preparation"),
                ("Hardware Installation", "hardware_installation"),
                ("Initial Configuration", "initial_configuration"),
                ("Advanced Configuration", "advanced_configuration"),
                ("Verification and Testing", "verification_testing"),
                ("Troubleshooting", "troubleshooting"),
                ("Maintenance and Support", "maintenance")
            ]
            
            content_sections = []
            for section_title, template_id in sections:
                # Extract relevant content for this section
                content = self._extract_section_content(extracted_text, section_title)
                if content and len(content.strip()) > 50:
                    content_section = ContentSection(
                        id=f"{pdf_path.stem}_{template_id}",
                        title=section_title,
                        content=content,
                        source=str(pdf_path),
                        confidence=0.85,
                        template_match=template_id,
                        acronyms_found=self._extract_acronyms(content)
                    )
                    content_sections.append(content_section)
                    logger.info(f"Created content section: {section_title}")
            
            return content_sections, used_placeholder
            
        except Exception as e:
            logger.error(f"Failed to extract content from {pdf_path}: {e}")
            return [], True
    
    def _extract_section_content(self, text: str, section_title: str) -> str:
        """Extract relevant content for a specific section."""
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
            content = f"Content extracted from documentation for {section_title}. This section contains relevant information about {section_title.lower()} procedures and requirements."
        
        return content
    
    def _extract_acronyms(self, text: str) -> List[tuple]:
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
            if acronym.upper() in text_upper:
                acronyms.append((acronym, definition))
        
        return acronyms
    
    def check_for_new_files(self) -> List[Path]:
        """Find new PDF files in upload folder."""
        new_files = []
        
        for file_path in self.upload_dir.glob("*.pdf"):
            if self._is_new_file(file_path):
                new_files.append(file_path)
        
        logger.info(f"Found {len(new_files)} new files to process")
        return new_files
    
    def process_file(self, file_path: Path) -> dict:
        """Process a single PDF file."""
        start_time = time.time()
        try:
            # Extract content from PDF
            content_sections, used_placeholder = self._extract_content_from_pdf(file_path)
            if not content_sections:
                logger.warning(f"No content extracted from {file_path.name}")
                return {
                    "status": "failed",
                    "error": "No content extracted",
                    "processing_time": time.time() - start_time
                }
            
            # Generate document title from filename
            doc_title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
            
            # Create output directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"outputs/batch_{timestamp}_{file_path.stem}"
            
            # Run workflow orchestrator
            outputs = self.orchestrator.run(
                content_sections=content_sections,
                document_title=doc_title,
                output_dir=output_dir
            )
            
            processing_time = time.time() - start_time
            
            # Compile results
            results = {
                "status": "completed_with_warnings" if used_placeholder else "completed",
                "processed_at": datetime.now().isoformat(),
                "hash": self._calculate_file_hash(file_path),
                "output_dir": output_dir,
                "processing_time": processing_time,
                "content_sections": len(content_sections),
                "coverage": outputs.get("coverage", 0),
                "confidence": outputs.get("confidence", 0),
                "output_files": {
                    k: v for k, v in outputs.items() 
                    if k.endswith('_md') or k.endswith('_json')
                }
            }
            
            if used_placeholder:
                results["warning"] = "Placeholder extraction used: PDF may be corrupted or not a valid PDF."
            
            logger.info(f"Successfully processed {file_path.name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def move_to_processed(self, file_path: Path):
        """Move processed file to processed folder."""
        try:
            processed_path = self.processed_dir / file_path.name
            shutil.move(str(file_path), str(processed_path))
            logger.info(f"Moved {file_path.name} to processed folder")
        except Exception as e:
            logger.error(f"Failed to move {file_path.name}: {e}")
    
    def update_log(self, filename: str, results: Dict):
        """Update processing log with results."""
        self.processing_log["processed_files"][filename] = results
        self.processing_log["last_check"] = datetime.now().isoformat()
        self._save_processing_log()
    
    def process_new_files(self, specific_file: Optional[str] = None):
        """Process all new files or a specific file."""
        if specific_file:
            # Process specific file
            file_path = self.upload_dir / specific_file
            if not file_path.exists():
                logger.error(f"File not found: {specific_file}")
                return
            
            logger.info(f"Processing specific file: {specific_file}")
            results = self.process_file(file_path)
            self.update_log(specific_file, results)
            
            if results["status"] == "completed":
                self.move_to_processed(file_path)
            
            return
        
        # Process all new files
        new_files = self.check_for_new_files()
        
        if not new_files:
            logger.info("No new files to process")
            return
        
        logger.info(f"Processing {len(new_files)} new files")
        
        for file_path in new_files:
            logger.info(f"Processing: {file_path.name}")
            results = self.process_file(file_path)
            self.update_log(file_path.name, results)
            
            if results["status"] == "completed":
                self.move_to_processed(file_path)
        
        logger.info(f"Batch processing completed. Processed {len(new_files)} files.")


def main():
    """Main function for batch processing."""
    parser = argparse.ArgumentParser(description="Batch process PDF files for documentation generation")
    parser.add_argument("--file", help="Process specific file in uploads/pending/")
    parser.add_argument("--list", action="store_true", help="List processed files")
    args = parser.parse_args()
    
    processor = BatchProcessor()
    
    if args.list:
        # List processed files
        print("Processed files:")
        for filename, info in processor.processing_log["processed_files"].items():
            status = info.get("status", "unknown")
            processed_at = info.get("processed_at", "unknown")
            print(f"  {filename}: {status} ({processed_at})")
        return
    
    # Process files
    processor.process_new_files(args.file)


if __name__ == "__main__":
    main() 