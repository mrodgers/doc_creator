# AI-Assisted Hardware Documentation Generation

A comprehensive system for generating hardware documentation using AI agents, automated gap analysis, and provenance tracking.

## 🚀 Features

- **Multi-Agent Architecture**: Managing Agent and Review Agent for comprehensive analysis
- **Automated Gap Analysis**: Identifies documentation gaps with actionable reports
- **Provenance Tracking**: Full traceability of information sources
- **Confidence Scoring**: Advanced confidence assessment with threshold-based triage
- **SME Question Generation**: Automated generation of questions for Subject Matter Experts
- **Web UI**: Minimal interface for confidence visualization and gap reports

## 📋 Requirements

- Python 3.9+
- uv package manager
- OpenAI API key or Anthropic API key
- Podman (for containerization)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-doc-gen
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   # or
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   ```

## 🏗️ Project Structure

```
ai-doc-gen/
├── src/
│   ├── ai_doc_gen/
│   │   ├── agents/           # Managing and Review agents
│   │   ├── input_processing/ # Document parsers and extractors
│   │   ├── core/            # Core functionality
│   │   ├── ui/              # Web interface
│   │   └── utils/           # Utilities and helpers
│   ├── tests/               # Test suite
│   └── docs/                # Documentation
├── examples/                # Sample inputs and outputs
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from ai_doc_gen.core.pipeline_orchestrator import PipelineOrchestrator

async def main():
    # Initialize pipeline
    config = {
        "llm_provider": "openai",
        "confidence_threshold": 85.0,
        "gap_threshold": 70.0
    }
    
    orchestrator = PipelineOrchestrator(config)
    
    # Run pipeline
    result = await orchestrator.run_pipeline(
        input_files=["path/to/document.pdf"],
        output_dir="output/",
        ground_truth="path/to/ground_truth.json"
    )
    
    print(f"Pipeline status: {result['status']}")

# Run the pipeline
asyncio.run(main())
```

### Using Individual Components

```python
from ai_doc_gen.core.llm_integration import LLMClient
from ai_doc_gen.core.confidence_scoring import ConfidenceScorer
from ai_doc_gen.core.gap_analyzer import GapAnalyzer

# Initialize components
llm_client = LLMClient(provider="openai")
confidence_scorer = ConfidenceScorer(default_threshold=85.0)
gap_analyzer = GapAnalyzer(confidence_threshold=70.0)

# Extract data with confidence scoring
async def extract_data():
    result = await llm_client.extract_structured_data(
        content="Your document content here",
        extraction_schema={"fields": ["field1", "field2"]}
    )
    return result
```

## 🔧 Configuration

### LLM Providers

The system supports multiple LLM providers:

- **OpenAI**: GPT-4o-mini, GPT-4o (default)
- **Anthropic**: Claude-3-Haiku, Claude-3-Sonnet

### Confidence Thresholds

- **Default Confidence Threshold**: 85% (auto-approval)
- **Gap Analysis Threshold**: 70% (identify gaps)
- **Review Threshold**: Below 85% (manual review)

## 📊 Outputs

The pipeline generates several outputs:

- **Generated Draft**: JSON format with structured content
- **Gap Report**: Comprehensive analysis of documentation gaps
- **Provenance Data**: Full traceability of information sources
- **Confidence Metrics**: Detailed confidence scoring
- **SME Questions**: Prioritized questions for Subject Matter Experts

## 🧪 Testing

Run the test suite:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov=src/ai_doc_gen
```

## 🐳 Docker Support

Build and run with Podman:

```bash
# Build image
podman build -t ai-doc-gen .

# Run container
podman run -it --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/data:/app/data \
  ai-doc-gen
```

## 📈 Metrics and Monitoring

The system provides comprehensive metrics:

- **Pipeline Performance**: Execution time, success rates
- **Confidence Analysis**: Average confidence, distribution
- **Gap Analysis**: Gap counts by severity and type
- **Provenance Tracking**: Source document reliability

## 🔄 Workflow

1. **Input Processing**: Parse PDF, DOCX, XML documents
2. **Managing Agent**: Extract specifications and generate initial analysis
3. **Gap Analysis**: Identify documentation gaps and generate SME questions
4. **Review Agent**: Validate provenance and cross-reference sources
5. **Draft Generation**: Create final documentation with confidence scores

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation in `docs/`
- Review example usage in `examples/`

## 🗺️ Roadmap

- [ ] Web UI implementation
- [ ] Graph database integration (Neo4j)
- [ ] Advanced template generation
- [ ] Multi-language support
- [ ] Enterprise integration features 