# AI Documentation Generation System

A comprehensive AI-powered documentation generation system with adaptive LLM matching, safety filters, cost tracking, and automated gap analysis.

## Features

### Core System
- **Adaptive LLM Matcher**: Self-evaluating and evolving prompt system
- **Safety Validation**: Input/output sanitization and filtering of suspicious patterns
- **Cost Tracking**: Comprehensive API usage monitoring and cost analysis
- **Provenance Tracking**: Full history of prompt evolution and decision-making
- **Document Processing**: Support for multiple document formats (PDF, DOCX, XML, HTML, etc.)

### AI Documentation Generation
- **Automated Draft Generation**: AI-driven documentation creation with ≥85% accuracy
- **Gap Analysis**: Automated identification of documentation gaps and missing information
- **SME Query Generation**: Intelligent question formulation for subject matter experts
- **Confidence Scoring**: Quality assessment and confidence metrics for generated content
- **Web UI**: Modern interface for document upload and result visualization

## Quick Start

### 🚀 **Easiest Way: Use the Launcher**
```bash
python launch_system.py
```
This will:
- Check if the system is running
- Open the web interface in your browser
- Provide quick start instructions

### 🔧 **Manual Setup**

1. Install dependencies:
```bash
uv sync
```

2. Start the containerized services:
```bash
cd ai-doc-gen
podman-compose up -d
```

3. Access the web interface:
```bash
# Open in browser: http://localhost:5432
```

4. Run tests:
```bash
uv run python -m pytest tests/
```

## User Experience

### **For Tech Writers:**
- **Web Interface**: Modern drag-and-drop interface at http://localhost:5432
- **Batch Processing**: Drop files in `uploads/pending/` for automated processing
- **Real-time Monitoring**: Track processing progress and view results
- **Output Dashboard**: Browse and manage generated documentation with `python output_dashboard.py`
- **Export Options**: Download generated documentation in multiple formats

### **For SMEs:**
- **Query Management**: Review and respond to automatically generated questions
- **Priority-based**: Questions are prioritized by importance and impact
- **Clear Context**: Each question includes relevant background information

## Architecture

The system consists of several key components:

### Adaptive LLM Matcher
- **AdaptiveMatcher**: Core matching engine with self-evaluation
- **SafetyValidator**: Input/output validation and sanitization
- **CostTracker**: API usage monitoring and cost analysis
- **DocumentParser**: Multi-format document processing
- **PromptEvolution**: Intelligent prompt improvement system

### AI Documentation Generator
- **Managing Agent**: Workflow orchestration and gap detection
- **Review Agent**: Provenance and confidence auditing
- **Input Processing**: Multi-format document parsing and extraction
- **Pipeline Orchestrator**: End-to-end workflow management
- **Web UI**: User interface for document processing

## Documentation

- `BATCH_PROCESSING.md` - Guide for batch file processing
- `PRD.md` - Product Requirements Document
- `DESIGN.md` - System architecture and design
- `DEVELOPMENT.md` - Development guidelines and setup

## License

MIT License
