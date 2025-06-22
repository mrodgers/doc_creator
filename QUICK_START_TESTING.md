# Quick Start Testing Guide

## 🚀 Get Started in 5 Minutes

### **Step 1: Setup Environment**
```bash
# Extract the deployment package
tar -xzf hardware_spec_extraction_pipeline_v1.0.tar.gz
cd hardware_spec_extraction_pipeline_v1.0

# Set up the environment
export OPENAI_API_KEY="your_api_key_here"
./deploy.sh
```

### **Step 2: Prepare Test Documents**
```bash
# Create test directories
mkdir -p test_documents
mkdir -p test_results
mkdir -p baseline_metrics

# Add your PDF documents to test_documents/
# Example: cp /path/to/your/hardware_guide.pdf test_documents/
```

### **Step 3: Create Ground Truth (Optional)**
For accurate testing, create ground truth files:
```bash
# Create ground truth JSON file for each document
# Example: ground_truth_your_device_name.json
{
  "specifications": [
    {
      "spec_item": "device_name",
      "value": "Your Device Model"
    },
    {
      "spec_item": "dimensions",
      "value": "17.3 x 1.7 x 19.2 in"
    }
    // ... add all 31 specification fields
  ]
}
```

### **Step 4: Run Your First Test**
```bash
# Test a single document
uv run pipeline_runner.py \
  --pdf test_documents/your_device.pdf \
  --ground_truth ground_truth_your_device.json \
  --output_dir test_results/your_device

# Or run automated batch testing
./test_runner.sh
```

### **Step 5: View Results**
```bash
# Generate performance dashboard
./performance_dashboard.sh

# View individual results
cat test_results/your_device/metrics.json | jq '.'
```

## 📊 Understanding Your Results

### **Key Metrics to Watch**
- **Coverage**: % of specs found (target: >95%)
- **Accuracy**: % of correct values (target: >85%)
- **Auto-Approval**: % of high-confidence specs (target: >90%)
- **Processing Time**: seconds per document (target: <30s)

### **Success Indicators**
✅ **Excellent**: Coverage >98%, Accuracy >95%
🟡 **Good**: Coverage >90%, Accuracy >80%
🔴 **Needs Work**: Coverage <90% or Accuracy <80%

## 🔧 Common Testing Scenarios

### **Scenario 1: Similar Hardware Types**
```bash
# Test multiple Cisco Nexus devices
for doc in test_documents/cisco_nexus_*.pdf; do
  device_name=$(basename "$doc" .pdf)
  uv run pipeline_runner.py \
    --pdf "$doc" \
    --ground_truth "ground_truth_${device_name}.json" \
    --output_dir "test_results/${device_name}"
done
```

### **Scenario 2: Different Vendors**
```bash
# Test across different vendors
for vendor in cisco juniper arista; do
  for doc in test_documents/${vendor}_*.pdf; do
    device_name=$(basename "$doc" .pdf)
    uv run pipeline_runner.py \
      --pdf "$doc" \
      --ground_truth "ground_truth_${device_name}.json" \
      --output_dir "test_results/${vendor}_${device_name}"
  done
done
```

### **Scenario 3: Performance Testing**
```bash
# Test processing time and resource usage
time uv run pipeline_runner.py \
  --pdf test_documents/large_document.pdf \
  --output_dir test_results/performance_test
```

## 🚨 Troubleshooting

### **Common Issues & Solutions**

#### **Issue: Low Coverage (<90%)**
**Symptoms**: Many specs not found
**Solutions**:
- Check PDF quality (not scanned)
- Verify document has Chapter 1 content
- Review extraction logs for errors

#### **Issue: Low Accuracy (<80%)**
**Symptoms**: Wrong values extracted
**Solutions**:
- Review ground truth format
- Check for vendor-specific terminology
- Update template rules in config.yaml

#### **Issue: High Review Rate (>15%)**
**Symptoms**: Many specs need manual review
**Solutions**:
- Lower confidence threshold in config
- Improve document quality
- Check for ambiguous specifications

### **Debug Commands**
```bash
# Check extraction quality
cat test_results/problematic_device/extracted_specs.json | jq '.[] | select(.confidence < 90)'

# Review low-confidence specs
cat test_results/problematic_device/extracted_specs_triage.json | jq '.review'

# Compare with ground truth
uv run quality_validation.py \
  --extracted test_results/problematic_device/corrected_specs.json \
  --ground ground_truth_problematic_device.json
```

## 📈 Continuous Testing

### **Daily Testing Workflow**
```bash
# 1. Run baseline tests
./test_runner.sh

# 2. Generate dashboard
./performance_dashboard.sh

# 3. Review results
open performance_dashboard.html

# 4. Check for regressions
diff baseline_metrics/test_summary.txt baseline_metrics/previous_summary.txt
```

### **Weekly Testing Schedule**
- **Monday**: Baseline validation
- **Tuesday**: New document types
- **Wednesday**: Edge case testing
- **Thursday**: Performance optimization
- **Friday**: Metrics analysis

## 🎯 Success Criteria

### **Minimum Viable Success**
- Coverage: >90% across all documents
- Accuracy: >80% across all documents
- Auto-approval: >85% across all documents
- Processing time: <60 seconds average

### **Production Ready**
- Coverage: >95% across all documents
- Accuracy: >90% across all documents
- Auto-approval: >90% across all documents
- Processing time: <30 seconds average

## 📞 Getting Help

### **When to Escalate**
- Coverage consistently <85%
- Accuracy consistently <75%
- Processing time >60 seconds
- Multiple test failures

### **Debugging Resources**
- Check logs in test_results/*/pipeline.log
- Review metrics.json for detailed breakdown
- Use performance_dashboard.html for visual analysis
- Consult DEVELOPER_TESTING_PLAN.md for detailed methodology

---

**Quick Start Version**: 1.0
**Last Updated**: January 2024 