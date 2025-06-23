#!/usr/bin/env python3
"""
Batch Processor for AI Documentation Generation

Processes PDF files from the uploads/pending directory and generates documentation.
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import error handler
try:
    from error_handler import ErrorHandler
except ImportError:
    print("⚠️  Error handler not found. Basic error handling will be used.")
    ErrorHandler = None

# Import PDF extractor
try:
    from pdf_extractor import PDFExtractor
except ImportError:
    print("❌ PDF extractor not found!")
    sys.exit(1)

# Import workflow orchestrator
try:
    from workflow_orchestrator import WorkflowOrchestrator
except ImportError:
    print("❌ Workflow orchestrator not found!")
    sys.exit(1)


class BatchProcessor:
    """Handles batch processing of PDF documents."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.uploads_dir = self.project_root / "uploads"
        self.pending_dir = self.uploads_dir / "pending"
        self.processed_dir = self.uploads_dir / "processed"
        self.outputs_dir = self.project_root / "outputs"
        self.log_file = self.project_root / "processing_log.json"
        
        self.error_handler = ErrorHandler() if ErrorHandler else None
        self.pdf_extractor = PDFExtractor()
        self.workflow = WorkflowOrchestrator()
        
        # Setup logging
        self.setup_logging()
        
        # Ensure directories exist
        self.ensure_directories()
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch_processing.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [self.uploads_dir, self.pending_dir, self.processed_dir, self.outputs_dir]
        
        for directory in directories:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created directory: {directory}")
                except Exception as e:
                    if self.error_handler:
                        self.error_handler.handle_error('permission_denied', 
                                                       f"Failed to create directory {directory}: {e}")
                    else:
                        self.logger.error(f"Failed to create directory {directory}: {e}")
                        raise
    
    def load_processing_log(self) -> Dict:
        """Load the processing log from JSON file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                if self.error_handler:
                    self.error_handler.handle_error('file_not_found', 
                                                   f"Failed to load processing log: {e}")
                else:
                    self.logger.warning(f"Failed to load processing log: {e}")
                return {}
        return {}
    
    def save_processing_log(self, log_data: Dict):
        """Save the processing log to JSON file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
        except IOError as e:
            if self.error_handler:
                self.error_handler.handle_error('permission_denied', 
                                               f"Failed to save processing log: {e}")
            else:
                self.logger.error(f"Failed to save processing log: {e}")
    
    def get_pending_files(self) -> List[Path]:
        """Get list of pending PDF files."""
        try:
            pdf_files = list(self.pending_dir.glob("*.pdf"))
            self.logger.info(f"Found {len(pdf_files)} pending PDF files")
            return pdf_files
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error('file_not_found', 
                                               f"Failed to scan pending directory: {e}")
            else:
                self.logger.error(f"Failed to scan pending directory: {e}")
            return []
    
    def validate_pdf_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validate that a PDF file is readable and not corrupted."""
        try:
            # Check file size
            if file_path.stat().st_size == 0:
                return False, "File is empty"
            
            # Try to extract text to validate PDF
            with open(file_path, 'rb') as f:
                # Read first few bytes to check PDF header
                header = f.read(4)
                if header != b'%PDF':
                    return False, "Not a valid PDF file (missing PDF header)"
            
            # Try to extract a small amount of text
            text = self.pdf_extractor.extract_text(str(file_path), max_pages=1)
            if not text or len(text.strip()) < 10:
                return False, "PDF appears to be empty or contains no readable text"
            
            return True, "Valid PDF file"
            
        except Exception as e:
            return False, f"PDF validation failed: {str(e)}"
    
    def process_single_file(self, file_path: Path) -> Dict:
        """Process a single PDF file."""
        file_info = {
            'filename': file_path.name,
            'filepath': str(file_path),
            'processed_at': datetime.now().isoformat(),
            'status': 'processing',
            'error': None,
            'output_files': [],
            'confidence_score': 0.0,
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Processing file: {file_path.name}")
            
            # Validate PDF file
            is_valid, validation_message = self.validate_pdf_file(file_path)
            if not is_valid:
                file_info['status'] = 'failed'
                file_info['error'] = validation_message
                if self.error_handler:
                    self.error_handler.handle_error('pdf_extraction_failed', 
                                                   f"{file_path.name}: {validation_message}")
                else:
                    self.logger.error(f"PDF validation failed for {file_path.name}: {validation_message}")
                return file_info
            
            # Extract text from PDF
            try:
                text_content = self.pdf_extractor.extract_text(str(file_path))
                if not text_content:
                    raise ValueError("No text content extracted from PDF")
            except Exception as e:
                file_info['status'] = 'failed'
                file_info['error'] = f"Text extraction failed: {str(e)}"
                if self.error_handler:
                    self.error_handler.handle_error('pdf_extraction_failed', 
                                                   f"{file_path.name}: {str(e)}")
                else:
                    self.logger.error(f"Text extraction failed for {file_path.name}: {e}")
                return file_info
            
            # Run workflow
            try:
                result = self.workflow.process_document(
                    filename=file_path.name,
                    content=text_content,
                    output_dir=self.outputs_dir
                )
                
                file_info['status'] = 'completed'
                file_info['confidence_score'] = result.get('confidence_score', 0.0)
                file_info['output_files'] = result.get('output_files', [])
                
                self.logger.info(f"Successfully processed {file_path.name}")
                
            except Exception as e:
                file_info['status'] = 'failed'
                file_info['error'] = f"Workflow processing failed: {str(e)}"
                if self.error_handler:
                    self.error_handler.handle_error('network_error', 
                                                   f"{file_path.name}: {str(e)}")
                else:
                    self.logger.error(f"Workflow processing failed for {file_path.name}: {e}")
            
        except Exception as e:
            file_info['status'] = 'failed'
            file_info['error'] = f"Unexpected error: {str(e)}"
            if self.error_handler:
                self.error_handler.handle_error('network_error', 
                                               f"{file_path.name}: {str(e)}")
            else:
                self.logger.error(f"Unexpected error processing {file_path.name}: {e}")
        
        finally:
            # Calculate processing time
            end_time = datetime.now()
            file_info['processing_time'] = (end_time - start_time).total_seconds()
        
        return file_info
    
    def move_processed_file(self, file_path: Path, success: bool):
        """Move processed file to appropriate directory."""
        try:
            if success:
                destination = self.processed_dir / file_path.name
            else:
                # Move failed files to a failed subdirectory
                failed_dir = self.processed_dir / "failed"
                failed_dir.mkdir(exist_ok=True)
                destination = failed_dir / file_path.name
            
            shutil.move(str(file_path), str(destination))
            self.logger.info(f"Moved {file_path.name} to {destination}")
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error('permission_denied', 
                                               f"Failed to move {file_path.name}: {e}")
            else:
                self.logger.error(f"Failed to move {file_path.name}: {e}")
    
    def run_batch_processing(self) -> Dict:
        """Run batch processing on all pending files."""
        print("🚀 Starting batch processing...")
        print("=" * 50)
        
        # Load existing log
        processing_log = self.load_processing_log()
        
        # Get pending files
        pending_files = self.get_pending_files()
        
        if not pending_files:
            print("✅ No pending files to process")
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        print(f"📄 Found {len(pending_files)} files to process")
        print("=" * 50)
        
        processed_count = 0
        successful_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(pending_files, 1):
            print(f"\n[{i}/{len(pending_files)}] Processing: {file_path.name}")
            
            # Process the file
            file_info = self.process_single_file(file_path)
            
            # Update processing log
            processing_log[file_path.name] = file_info
            
            # Move file to processed directory
            success = file_info['status'] == 'completed'
            self.move_processed_file(file_path, success)
            
            # Update counters
            processed_count += 1
            if success:
                successful_count += 1
                print(f"✅ Success: {file_path.name} (Confidence: {file_info['confidence_score']:.1%})")
            else:
                failed_count += 1
                print(f"❌ Failed: {file_path.name} - {file_info['error']}")
        
        # Save updated log
        self.save_processing_log(processing_log)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 BATCH PROCESSING SUMMARY")
        print("=" * 50)
        print(f"📄 Total files processed: {processed_count}")
        print(f"✅ Successful: {successful_count}")
        print(f"❌ Failed: {failed_count}")
        
        if successful_count > 0:
            success_rate = (successful_count / processed_count) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        if failed_count > 0:
            print(f"\n⚠️  Failed files moved to: {self.processed_dir}/failed/")
        
        print(f"📁 Output files: {self.outputs_dir}")
        print(f"📋 Processing log: {self.log_file}")
        print("=" * 50)
        
        return {
            'processed': processed_count,
            'successful': successful_count,
            'failed': failed_count
        }


def main():
    """Main function."""
    try:
        processor = BatchProcessor()
        result = processor.run_batch_processing()
        
        if result['failed'] > 0:
            sys.exit(1)  # Exit with error code if any files failed
        else:
            sys.exit(0)  # Exit successfully
            
    except KeyboardInterrupt:
        print("\n⚠️  Batch processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if processor and processor.error_handler:
            processor.error_handler.handle_error('network_error', str(e))
        sys.exit(1)


if __name__ == "__main__":
    main() 