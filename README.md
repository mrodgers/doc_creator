# AI-Assisted Hardware Documentation Generation System

An intelligent system for automatically generating hardware installation documentation from Cisco product PDFs with ≥85% accuracy, gap analysis, and provenance tracking.

## 🚀 Quick Start

### 1. Launch the System
```bash
python launch_system.py
```

This interactive launcher provides:
- **System Status**: Check if services are running
- **Start/Stop Services**: Manage the web UI and database
- **Web Interface**: Open the browser automatically (default: http://localhost:5476)
- **Batch Processing**: Process multiple PDF files
- **Output Dashboard**: View generated documentation
- **Health Check**: Diagnose system issues

### 2. Upload Documents
- **Web UI**: Drag & drop PDFs at http://localhost:5476
- **Batch Processing**: Place PDFs in `uploads/pending/` and run batch processor

### 3. View Results
- **Web Dashboard**: Real-time processing status
- **Output Dashboard**: Browse generated documentation
- **Output Files**: Check `outputs/` directory

## 🆕 New Features

### Interactive Gap Analysis Dashboard
- **Access**: Navigate to "Gap Analysis" in the web UI
- **Features**:
  - Interactive gap visualization with severity indicators
  - Clickable gap items with status tracking
  - User feedback collection on gap resolution
  - Real-time gap status updates
  - Export learning data for system improvement

### User Feedback Collection System
- **Document Feedback**: Embedded feedback widgets in generated documentation
- **Multi-dimensional Ratings**: Quality, accuracy, completeness, and clarity
- **Learning Retention**: System learns from user feedback to improve future generations
- **Feedback Analytics**: Track performance trends and identify improvement areas

### Enhanced User Experience
- **Real-time Processing**: Live progress indicators and status updates
- **Interactive Dashboards**: Visual feedback and analytics
- **Error Handling**: Comprehensive error messages with recovery suggestions
- **Configurable Ports**: Non-conflicting port system (default: 5476)

## 📊 System Capabilities

### Core Features
- **AI-Powered Generation**: ≥85% accuracy documentation generation
- **Gap Analysis**: Automated identification of documentation gaps
- **Provenance Tracking**: Full traceability of information sources
- **Batch Processing**: Handle multiple documents efficiently
- **Multi-format Export**: Markdown, PDF, and structured data

### Advanced Features
- **Interactive Gap Management**: Visual gap analysis with user feedback
- **Learning System**: Continuous improvement through user feedback
- **Performance Analytics**: Track system performance and user satisfaction
- **Export Capabilities**: Learning data export for system improvement

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional (with defaults)
WEB_PORT=5476                    # Web UI port
CONFIDENCE_THRESHOLD=85.0        # Minimum confidence for generation
GAP_THRESHOLD=70.0              # Minimum gap detection threshold
LOG_LEVEL=INFO                  # Logging level
```

### Port Configuration
- **Default Web UI Port**: 5476 (non-conflicting)
- **Change Port**: Set `WEB_PORT` environment variable
- **Neo4j Ports**: 7474 (HTTP), 7687 (Bolt)

## 📁 Project Structure

```
ai-doc-gen/
├── src/ai_doc_gen/
│   ├── core/                   # Core pipeline components
│   ├── ui/                     # Web interface
│   │   ├── gap_dashboard.py    # Interactive gap analysis
│   │   └── templates/          # HTML templates
│   ├── feedback/               # Feedback collection system
│   └── utils/                  # Utility modules
├── outputs/                    # Generated documentation
├── uploads/                    # Input documents
├── feedback/                   # User feedback data
└── tests/                      # Test suite
```

## 🎯 User Workflows

### 1. Document Processing
1. Upload PDF document via web UI or batch processor
2. System processes document and generates draft
3. Review generated documentation and gap analysis
4. Provide feedback on quality and gaps

### 2. Gap Analysis & Feedback
1. Access "Gap Analysis" dashboard
2. Review identified gaps with severity indicators
3. Mark gaps as resolved, in progress, or ignored
4. Provide detailed feedback on gap resolution
5. Export learning data for system improvement

### 3. System Learning
1. System collects user feedback on document quality
2. Analyzes feedback patterns and common issues
3. Identifies improvement areas and success patterns
4. Uses insights to enhance future document generation

## 🧪 Testing

### Run System Tests
```bash
cd ai-doc-gen
uv run pytest tests/ -v
```

### Demo New Features
```bash
python feedback_demo.py
```

### Test Web Interface
```bash
# Test gap dashboard
curl http://localhost:5476/gaps

# Test feedback API
curl http://localhost:5476/api/feedback/summary
```

## 🚨 Error Handling

The system includes comprehensive error handling with user-friendly messages:

### Common Issues & Solutions

#### 🔌 Port Conflict
**Problem**: Port 5476 already in use
**Solution**: 
```bash
lsof -i :5476  # Check what's using the port
# Stop conflicting service or change port in docker-compose.yml
```

#### 🐳 Container Issues
**Problem**: Podman containers not starting
**Solution**:
```bash
podman machine restart
podman-compose up -d
```

#### 🔑 API Key Missing
**Problem**: OpenAI API key not configured
**Solution**:
```bash
export OPENAI_API_KEY='your-key-here'
```

#### 💾 Disk Space
**Problem**: Insufficient disk space for processing
**Solution**:
```bash
podman system prune -a -f  # Clean up containers
# Free up additional space as needed
```

## 📈 Performance Metrics

### Current Performance
- **Documentation Accuracy**: ≥85%
- **Gap Detection**: Comprehensive coverage
- **Processing Speed**: ~10-15 seconds per document
- **User Satisfaction**: Tracked via feedback system

### Learning Metrics
- **Feedback Collection**: Multi-dimensional ratings
- **Gap Resolution Rate**: Tracked per document
- **System Improvement**: Continuous learning from user feedback
- **Performance Trends**: Analytics dashboard

## 🔮 Future Enhancements

### Planned Features
- **Advanced Analytics Dashboard**: Real-time performance metrics
- **Template Customization**: User-configurable documentation templates
- **SME Query Management**: Interactive question-answer system
- **Version Control**: Document versioning and comparison
- **API Integration**: External tool integration capabilities

### Learning & Adaptation
- **Feedback-Driven Optimization**: Continuous system improvement
- **Domain-Specific Learning**: Specialized knowledge for different product types
- **Automated Quality Assurance**: Enhanced validation and consistency checks
- **Collaborative Workflows**: Multi-user feedback and review systems

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies with `uv sync`
3. Set up environment variables
4. Run tests with `uv run pytest`

### Code Quality
- **Linting**: `uv run ruff check`
- **Testing**: `uv run pytest`
- **Type Checking**: `uv run mypy src/`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
1. Check the error handling section above
2. Review system logs: `podman logs ai-doc-gen-dev`
3. Run health check: `python error_handler.py`
4. Test system: `python launch_system.py`

### System Status
- **Web UI**: http://localhost:5476
- **Neo4j Browser**: http://localhost:7474
- **Container Status**: `podman ps`
- **System Health**: `python error_handler.py`
