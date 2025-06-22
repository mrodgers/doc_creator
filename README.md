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
- **Web UI**: Minimal interface for document upload and result visualization

## Quick Start

1. Install dependencies:
```bash
uv sync
```

2. Run the adaptive matcher:
```bash
uv run python adaptive-llm-matcher/adaptive_llm_matcher.py
```

3. Run the AI documentation generator:
```bash
cd ai-doc-gen
uv run python launch_ui.py
```

4. Run tests:
```bash
uv run python -m pytest tests/
```

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

- `ADAPTIVE_LLM_APPROACH.md` - Detailed technical documentation for adaptive matching
- `PRD.md` - Product Requirements Document
- `DESIGN.md` - System architecture and design
- `DEVELOPMENT.md` - Development guidelines and setup

## License

MIT License
