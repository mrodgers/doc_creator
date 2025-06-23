# Hardware Specification Extraction Pipeline - Run Book

## 🎯 Overview

This run-book describes how to operate the automated hardware specification extraction pipeline. The system extracts specifications from Cisco hardware installation PDFs, applies confidence scoring, and generates templated documentation.

## 📋 Prerequisites

### Required Software
- Python 3.9+
- `uv` package manager
- OpenAI API key

### Required Files
- Hardware installation PDF (e.g., `cisco-nexus-9364c_h1_aci_mode_hardware_install_guide.pdf`)
- Ground truth specifications JSON file
- Template rules configuration (`template_rules.yaml`)

### Environment Setup
```bash
# Set OpenAI API key
export OPENAI_API_KEY="your_api_key_here"

# Install dependencies
uv sync
```

## 🚀 Launching the Pipeline

### Basic Pipeline Run
```bash
uv run pipeline_runner.py \
  --pdf cisco-nexus-9364c_h1_aci_mode_hardware_install_guide.pdf \
  --ground_truth ground_truth_specs.json \
  --output_dir pipeline_output
```

### Pipeline Steps
1. **Chapter Extraction**: Extracts Chapter 1 content from PDF
2. **Spec Extraction**: Extracts 31 specifications with confidence scores
3. **Audit**: Reviews low-confidence specs (if any)
4. **Template Generation**: Creates templated documentation
5. **Markdown Rendering**: Generates final markdown output
6. **Quality Validation**: Validates against ground truth
7. **Metrics Export**: Saves comprehensive performance metrics

## 📊 Interpreting the Dashboard

### Key Metrics Dashboard

After each run, the system generates a `metrics.json` file with comprehensive performance data:

#### **Pipeline Performance**
```json
{
  "pipeline_run": {
    "timestamp": "2024-01-15T10:30:00",
    "duration_seconds": 45.2,
    "pdf_source": "cisco-nexus-9364c_h1_aci_mode_hardware_install_guide.pdf",
    "output_directory": "pipeline_output"
  }
}
```

#### **Confidence Metrics**
```json
{
  "confidence_metrics": {
    "threshold": 90,
    "total_specs": 31,
    "auto_approved": 30,
    "review_needed": 1,
    "auto_approval_rate": 96.8,
    "review_rate": 3.2,
    "average_confidence": 91.6,
    "confidence_distribution": {
      "90-100": 30,
      "70-89": 1,
      "50-69": 0,
      "30-49": 0,
      "0-29": 0
    }
  }
}
```

#### **Quality Metrics**
```json
{
  "quality_metrics": {
    "ground_truth_specs": 31,
    "extracted_specs": 31,
    "matched_specs": 27,
    "coverage_percent": 100.0,
    "accuracy_percent": 87.10
  }
}
```

### **Performance Indicators**

| Metric | Excellent | Good | Needs Attention | Critical |
|--------|-----------|------|-----------------|----------|
| **Coverage** | 100% | 95-99% | 90-94% | <90% |
| **Accuracy** | >95% | 85-95% | 75-84% | <75% |
| **Auto-Approval Rate** | >95% | 85-95% | 70-84% | <70% |
| **Average Confidence** | >90% | 80-90% | 70-79% | <70% |
| **Review Rate** | <5% | 5-15% | 15-30% | >30% |

## 🚨 Handling Low-Confidence Alerts

### **Alert Types**

#### **1. High Review Rate (>15%)**
**Symptoms**: Many specs requiring manual review
**Actions**:
- Check PDF quality and formatting
- Review template rules for missing patterns
- Consider lowering confidence threshold temporarily
- Investigate specific low-confidence specs

#### **2. Low Accuracy (<85%)**
**Symptoms**: Poor match with ground truth
**Actions**:
- Review audit results for systematic errors
- Check ground truth file for accuracy
- Investigate specific mismatched specs
- Consider prompt engineering improvements

#### **3. Low Coverage (<95%)**
**Symptoms**: Missing specifications
**Actions**:
- Check PDF content completeness
- Review extraction prompts
- Verify ground truth completeness
- Check for PDF parsing issues

### **Troubleshooting Workflow**

#### **Step 1: Identify the Issue**
```bash
# Check metrics summary
cat pipeline_output/metrics.json | jq '.confidence_metrics'
cat pipeline_output/metrics.json | jq '.quality_metrics'
```

#### **Step 2: Review Low-Confidence Specs**
```bash
# Check which specs need review
cat pipeline_output/extracted_specs_triage.json | jq '.review'
```

#### **Step 3: Investigate Specific Issues**
```bash
# Compare extracted vs ground truth
uv run quality_validation.py \
  --extracted pipeline_output/corrected_specs.json \
  --ground ground_truth_specs.json
```

#### **Step 4: Manual Review Process**
1. **Review triage results**: Check `extracted_specs_triage.json`
2. **Examine low-confidence specs**: Look at confidence scores <90%
3. **Check audit results**: Review `corrected_specs.json` for confidence boosts
4. **Validate manually**: Compare with source PDF

### **Common Issues & Solutions**

#### **Issue: High Review Rate**
**Cause**: Ambiguous or unclear specifications in PDF
**Solution**: 
- Lower confidence threshold to 85%
- Add more specific template rules
- Improve extraction prompts

#### **Issue: Low Accuracy**
**Cause**: Systematic extraction errors
**Solution**:
- Review audit results
- Check for unit conversion issues
- Verify part number formatting
- Update template rules

#### **Issue: Missing Specs**
**Cause**: PDF parsing or content issues
**Solution**:
- Check PDF quality
- Review chapter extraction
- Verify ground truth completeness

## 🔧 Configuration Management

### **Template Rules**
Location: `template_rules.yaml`
```yaml
rules:
  - pattern: "Cisco Nexus 9364C-H1 switch"
    replacement: "{{Product name}}"
    priority: 1
```

### **Confidence Threshold**
Default: 90%
- **High threshold (90%)**: Stricter quality, more manual review
- **Low threshold (80%)**: More automation, potential quality trade-offs

### **Audit Configuration**
- **Auto-audit**: Runs automatically on low-confidence specs
- **Manual audit**: Can be triggered separately
- **Confidence boost**: Audited specs get 95% confidence

## 📈 Monitoring & Analytics

### **Performance Tracking**
Track these metrics over time:
- Average confidence per guide
- Review rate trends
- Accuracy improvements
- Processing time optimization

### **Quality Assurance**
- Regular ground truth validation
- Cross-reference with official documentation
- Monitor confidence distribution patterns
- Track audit effectiveness

### **Continuous Improvement**
- Analyze low-confidence patterns
- Update template rules based on findings
- Refine extraction prompts
- Optimize confidence thresholds

## 🆘 Emergency Procedures

### **Pipeline Failure**
1. Check error logs in output directory
2. Verify API key and connectivity
3. Check file permissions and disk space
4. Restart with clean output directory

### **Low Quality Results**
1. Review confidence metrics
2. Check PDF source quality
3. Validate ground truth accuracy
4. Consider manual intervention

### **API Rate Limits**
1. Check OpenAI API usage
2. Implement rate limiting
3. Use alternative models if needed
4. Batch processing for large volumes

## 📞 Support & Escalation

### **Level 1: Self-Service**
- Check this run-book
- Review metrics and logs
- Basic troubleshooting

### **Level 2: Technical Support**
- Complex configuration issues
- Performance optimization
- Template rule updates

### **Level 3: Development**
- Pipeline modifications
- New feature requests
- Architecture changes

## 📚 Additional Resources

- **Configuration Files**: `template_rules.yaml`, `unit_rules.yaml`
- **Test Suite**: `test_confidence_scoring.py`, `test_unit_rules.py`
- **Documentation**: `confidence_scoring_summary.md`
- **Examples**: `pipeline_output/` directories

---

**Last Updated**: June 2025
**Version**: 1.0
**Maintainer**: AI Assistant 