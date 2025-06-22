#!/bin/bash

# Hardware Specification Extraction Pipeline - Deployment Script
# This script sets up the production environment

set -e  # Exit on any error

echo "🚀 Hardware Specification Extraction Pipeline - Deployment"
echo "=========================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION"

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv package manager is required but not installed"
    echo "📥 Install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "✅ uv package manager found"

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY environment variable not set"
    echo "📝 Please set your OpenAI API key:"
    echo "   export OPENAI_API_KEY='your_api_key_here'"
    echo ""
    echo "🔑 You can get an API key from: https://platform.openai.com/api-keys"
    exit 1
fi

echo "✅ OpenAI API key configured"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
uv sync

# Run tests
echo ""
echo "🧪 Running test suite..."

echo "Testing confidence scoring..."
uv run test_confidence_scoring.py

echo "Testing template rules..."
uv run test_unit_rules.py

echo "Testing markdown renderer..."
uv run test_renderer.py

echo ""
echo "✅ All tests passed!"

# Create sample output directory
echo ""
echo "📁 Creating sample output directory..."
mkdir -p sample_output

# Display success message
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Review the documentation:"
echo "   - README.md - Quick start guide"
echo "   - RUNBOOK.md - Operational guide"
echo "   - METRICS_GUIDE.md - Metrics interpretation"
echo ""
echo "2. Test the pipeline:"
echo "   uv run pipeline_runner.py \\"
echo "     --pdf your_hardware_guide.pdf \\"
echo "     --ground_truth ground_truth_specs.json \\"
echo "     --output_dir sample_output"
echo ""
echo "3. Monitor performance:"
echo "   cat sample_output/metrics.json | jq '.confidence_metrics'"
echo ""
echo "📞 For support, check RUNBOOK.md for troubleshooting guides"
echo ""
echo "🚀 System is ready for production use!" 