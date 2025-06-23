#!/usr/bin/env python3
"""
Test script for batch processor functionality.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys_path_entry = str(Path(__file__).parent / 'ai-doc-gen' / 'src')
print(f"Adding to sys.path: {sys_path_entry}")
sys.path.insert(0, sys_path_entry)

from batch_processor import BatchProcessor


def create_test_pdf():
    """Create a simple test PDF file."""
    # Create a temporary PDF-like file for testing
    test_content = """
    Hardware Overview
    
    This section provides an overview of the Cisco Nexus 9000 Series switches.
    The switches support various port configurations and power options.
    
    Installation Preparation
    
    Before installing the hardware, ensure you have the necessary tools and
    documentation. Check the site requirements and power specifications.
    
    Hardware Installation
    
    Follow these steps to install the hardware:
    1. Unpack the equipment
    2. Mount the switch in the rack
    3. Connect power cables
    4. Connect network cables
    
    Initial Configuration
    
    After hardware installation, perform initial configuration:
    - Set up basic network parameters
    - Configure management interface
    - Enable required services
    
    Advanced Configuration
    
    For advanced features, configure:
    - VLAN settings
    - QoS policies
    - Security features
    - Monitoring and logging
    
    Verification and Testing
    
    Test the installation by:
    - Verifying power status
    - Checking network connectivity
    - Running diagnostic commands
    - Validating configuration
    
    Troubleshooting
    
    Common issues and solutions:
    - Power problems: Check power supply and cables
    - Network issues: Verify cable connections and configuration
    - Performance problems: Monitor system resources
    
    Maintenance and Support
    
    Regular maintenance includes:
    - Software updates
    - Hardware inspection
    - Performance monitoring
    - Backup configuration
    """
    
    # Create a temporary file with .pdf extension
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.write(test_content.encode('utf-8'))
    temp_file.close()
    
    return temp_file.name


def test_batch_processor_basic():
    """Test basic batch processor functionality."""
    print("Testing basic batch processor functionality...")
    
    # Create test directories
    test_upload_dir = Path("test_uploads/pending")
    test_processed_dir = Path("test_uploads/processed")
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    test_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    test_pdf_name = "test_nexus_9000.pdf"
    shutil.copy(test_pdf_path, test_upload_dir / test_pdf_name)
    
    # Clean up temporary file
    os.unlink(test_pdf_path)
    
    # Mock the PDF extractor and workflow orchestrator
    with patch('batch_processor.PDFExtractor') as mock_extractor_class, \
         patch('batch_processor.WorkflowOrchestrator') as mock_orchestrator_class:
        
        # Mock PDF extractor
        mock_extractor = MagicMock()
        mock_extractor.extract_text.return_value = """
        Hardware Overview
        This section provides an overview of the Cisco Nexus 9000 Series switches.
        Installation Preparation
        Before installing the hardware, ensure you have the necessary tools.
        Hardware Installation
        Follow these steps to install the hardware.
        """
        mock_extractor_class.return_value = mock_extractor
        
        # Mock workflow orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.run.return_value = {
            "coverage": 100.0,
            "confidence": 0.95,
            "draft_md": "test_uploads/processed/test_output.md",
            "gap_analysis_json": "test_uploads/processed/test_gaps.json"
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create processor with test directories
        processor = BatchProcessor()
        processor.upload_dir = test_upload_dir
        processor.processed_dir = test_processed_dir
        processor.log_file = Path("test_processing_log.json")
        
        # Test processing
        processor.process_new_files()
        
        # Verify results
        assert (test_processed_dir / test_pdf_name).exists(), "File should be moved to processed folder"
        assert processor.log_file.exists(), "Processing log should be created"
        
        # Check log contents
        with open(processor.log_file, 'r') as f:
            import json
            log_data = json.load(f)
            assert test_pdf_name in log_data["processed_files"], "File should be in processing log"
            assert log_data["processed_files"][test_pdf_name]["status"] == "completed", "File should be marked as completed"
        
        print("✓ Basic batch processor test passed")
    
    # Cleanup
    shutil.rmtree("test_uploads", ignore_errors=True)
    if Path("test_processing_log.json").exists():
        os.unlink("test_processing_log.json")


def test_batch_processor_file_detection():
    """Test file detection and hash calculation."""
    print("Testing file detection and hash calculation...")
    
    # Create test directories
    test_upload_dir = Path("test_uploads/pending")
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    test_pdf_name = "test_detection.pdf"
    shutil.copy(test_pdf_path, test_upload_dir / test_pdf_name)
    
    # Clean up temporary file
    os.unlink(test_pdf_path)
    
    processor = BatchProcessor()
    processor.upload_dir = test_upload_dir
    processor.log_file = Path("test_detection_log.json")
    
    # Test new file detection
    file_path = test_upload_dir / test_pdf_name
    assert processor._is_new_file(file_path), "New file should be detected"
    
    # Test hash calculation
    hash_value = processor._calculate_file_hash(file_path)
    assert len(hash_value) == 64, "SHA-256 hash should be 64 characters"
    assert hash_value != "hash_calculation_failed", "Hash calculation should succeed"
    
    # Test duplicate file detection
    processor.update_log(test_pdf_name, {"status": "completed", "hash": hash_value})
    assert not processor._is_new_file(file_path), "Processed file should not be detected as new"
    
    print("✓ File detection test passed")
    
    # Cleanup
    shutil.rmtree("test_uploads", ignore_errors=True)
    if Path("test_detection_log.json").exists():
        os.unlink("test_detection_log.json")


def test_batch_processor_content_extraction():
    """Test content extraction from PDF."""
    print("Testing content extraction...")
    
    processor = BatchProcessor()
    
    # Test section content extraction
    test_text = """
    Hardware Overview
    This is the hardware overview section with important information.
    
    Installation Preparation
    This section covers installation preparation steps.
    
    Hardware Installation
    Follow these installation steps carefully.
    """
    
    # Test extraction for different sections
    sections = [
        ("Hardware Overview", "hardware_overview"),
        ("Installation Preparation", "installation_preparation"),
        ("Hardware Installation", "hardware_installation")
    ]
    
    for section_title, template_id in sections:
        content = processor._extract_section_content(test_text, section_title)
        assert content, f"Content should be extracted for {section_title}"
        assert section_title.lower() in content.lower(), f"Section title should be in extracted content for {section_title}"
        print(f"  ✓ Extracted content for {section_title}")
    
    # Test acronym extraction
    test_text_with_acronyms = """
    Configure VLAN settings and QoS policies. Use SNMP for monitoring.
    Enable SSH access and configure TFTP for file transfers.
    """
    
    acronyms = processor._extract_acronyms(test_text_with_acronyms)
    print(f"Found acronyms: {acronyms}")
    expected_acronyms = ['VLAN', 'QoS', 'SNMP', 'SSH', 'TFTP']
    
    found_acronyms = [acronym for acronym, _ in acronyms]
    for expected in expected_acronyms:
        assert expected in found_acronyms, f"Acronym {expected} should be detected"
    
    print("✓ Content extraction test passed")


def test_batch_processor_error_handling():
    """Test error handling in batch processor."""
    print("Testing error handling...")
    
    # Create test directories
    test_upload_dir = Path("test_uploads/pending")
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a non-PDF file
    test_file_name = "test_file.txt"
    with open(test_upload_dir / test_file_name, 'w') as f:
        f.write("This is not a PDF file")
    
    processor = BatchProcessor()
    processor.upload_dir = test_upload_dir
    processor.log_file = Path("test_error_log.json")
    
    # Test processing non-PDF file (should be ignored)
    new_files = processor.check_for_new_files()
    assert len(new_files) == 0, "Non-PDF files should be ignored"
    
    # Test processing with mocked failure
    with patch('batch_processor.PDFExtractor') as mock_extractor_class:
        mock_extractor = MagicMock()
        mock_extractor.extract_text.side_effect = Exception("PDF extraction failed")
        mock_extractor_class.return_value = mock_extractor
        
        # Create a test PDF file
        test_pdf_path = create_test_pdf()
        test_pdf_name = "test_error.pdf"
        shutil.copy(test_pdf_path, test_upload_dir / test_pdf_name)
        os.unlink(test_pdf_path)
        
        # Process file (should handle error gracefully)
        results = processor.process_file(test_upload_dir / test_pdf_name)
        assert results["status"] == "completed_with_warnings", "Processing should complete with warnings for bad PDFs"
        assert "warning" in results, "Warning should be present in results for placeholder extraction"
        
        print("✓ Error handling test passed")
    
    # Cleanup
    shutil.rmtree("test_uploads", ignore_errors=True)
    if Path("test_error_log.json").exists():
        os.unlink("test_error_log.json")


def main():
    """Run all tests."""
    print("Running batch processor tests...\n")
    
    try:
        test_batch_processor_basic()
        print()
        test_batch_processor_file_detection()
        print()
        test_batch_processor_content_extraction()
        print()
        test_batch_processor_error_handling()
        print()
        
        print("🎉 All batch processor tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main() 