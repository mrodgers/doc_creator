# Batch Processing System

## Overview

The batch processing system provides a simple way to automatically process PDF files for AI-assisted documentation generation. It monitors an upload folder, processes new files, and tracks what has been processed.

## Features

- **Simple folder structure**: `uploads/pending/` for new files, `uploads/processed/` for completed files
- **File tracking**: Uses SHA-256 hashes to detect new or updated files
- **Processing log**: JSON file tracks all processed files with metadata
- **Batch processing**: Process all new files at once or specific files individually
- **Error handling**: Graceful handling of processing failures
- **Resumable**: Can restart and continue from where it left off

## Usage

### Basic Usage

1. **Place PDF files** in `uploads/pending/` folder
2. **Run batch processor**:
   ```bash
   uv run python batch_processor.py
   ```
3. **Check results** in `outputs/` folder and `processing_log.json`

### Command Line Options

```bash
# Process all new files
uv run python batch_processor.py

# Process specific file
uv run python batch_processor.py --file "nexus_9000_guide.pdf"

# List processed files
uv run python batch_processor.py --list
```

### Folder Structure

```
uploads/
├── pending/          # New PDF files to process
│   ├── file1.pdf
│   └── file2.pdf
└── processed/        # Completed files
    ├── file1.pdf
    └── file2.pdf

outputs/              # Generated documentation
├── batch_20241201_143022_file1/
│   ├── draft.md
│   ├── gap_analysis.json
│   └── provenance.json
└── batch_20241201_143045_file2/
    ├── draft.md
    ├── gap_analysis.json
    └── provenance.json

processing_log.json   # Processing history and metadata
```

## Processing Log

The `processing_log.json` file tracks all processed files:

```json
{
  "processed_files": {
    "nexus_9000_guide.pdf": {
      "status": "completed",
      "processed_at": "2024-12-01T14:30:22.123456",
      "hash": "a1b2c3d4...",
      "output_dir": "outputs/batch_20241201_143022_nexus_9000_guide",
      "processing_time": 45.2,
      "content_sections": 8,
      "coverage": 100.0,
      "confidence": 0.95,
      "output_files": {
        "draft_md": "outputs/batch_20241201_143022_nexus_9000_guide/draft.md",
        "gap_analysis_json": "outputs/batch_20241201_143022_nexus_9000_guide/gap_analysis.json"
      }
    }
  },
  "last_check": "2024-12-01T14:30:22.123456"
}
```

## Testing

Run the test suite to verify functionality:

```bash
uv run python test_batch_processor.py
```

Tests cover:
- Basic file processing
- File detection and hash calculation
- Content extraction
- Error handling

## Integration

The batch processor integrates with the existing AI documentation generation system:

1. **PDF Extraction**: Uses `PDFExtractor` to extract text content
2. **Content Analysis**: Creates `ContentSection` objects for each documentation section
3. **Workflow Orchestration**: Uses `WorkflowOrchestrator` to generate documentation
4. **Output Generation**: Creates markdown drafts, gap analysis, and provenance tracking

## Monitoring

To monitor the system:

1. **Check processing log**: `uv run python batch_processor.py --list`
2. **Review output files**: Generated documentation in `outputs/` folders
3. **Monitor upload folder**: New files in `uploads/pending/`
4. **Check processed files**: Completed files in `uploads/processed/`

## Error Recovery

If processing fails:

1. **Check error details** in `processing_log.json`
2. **Fix the issue** (e.g., corrupted PDF, network problems)
3. **Re-run processor**: `uv run python batch_processor.py`
4. **Files will be reprocessed** if they have different hashes

## Automation

For continuous processing, you can:

1. **Set up a cron job** to run the processor periodically
2. **Use file system watchers** to trigger processing on new files
3. **Integrate with CI/CD** for automated documentation generation

Example cron job (every 5 minutes):
```bash
*/5 * * * * cd /path/to/ai-doc-gen && uv run python batch_processor.py
``` 