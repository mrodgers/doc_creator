#!/bin/bash
# test_runner.sh - Automated testing script for hardware specification extraction pipeline

set -e  # Exit on any error

# Configuration
TEST_DOCS_DIR="test_documents"
RESULTS_DIR="test_results"
BASELINE_DIR="baseline_metrics"
LOG_FILE="test_run_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directories if they don't exist
mkdir -p "$TEST_DOCS_DIR"
mkdir -p "$RESULTS_DIR"
mkdir -p "$BASELINE_DIR"

echo "=== Hardware Specification Extraction Pipeline Test Runner ===" | tee "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "Test Documents Directory: $TEST_DOCS_DIR" | tee -a "$LOG_FILE"
echo "Results Directory: $RESULTS_DIR" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check if test documents exist
if [ ! "$(ls -A $TEST_DOCS_DIR)" ]; then
    echo -e "${RED}Error: No test documents found in $TEST_DOCS_DIR${NC}" | tee -a "$LOG_FILE"
    echo "Please add PDF documents to test against." | tee -a "$LOG_FILE"
    exit 1
fi

# Initialize results summary
echo "=== Test Results Summary ===" > "$BASELINE_DIR/test_summary.txt"
echo "Test Run: $(date)" >> "$BASELINE_DIR/test_summary.txt"
echo "" >> "$BASELINE_DIR/test_summary.txt"
echo "Device Name | Coverage | Accuracy | Auto-Approval | Duration | Status" >> "$BASELINE_DIR/test_summary.txt"
echo "-----------|----------|----------|---------------|----------|--------" >> "$BASELINE_DIR/test_summary.txt"

# Initialize metrics aggregation
declare -a coverage_scores
declare -a accuracy_scores
declare -a auto_approval_scores
declare -a duration_scores
declare -a test_names

test_count=0
success_count=0
failure_count=0

# Function to run a single test
run_single_test() {
    local doc="$1"
    local device_name=$(basename "$doc" .pdf)
    local result_dir="$RESULTS_DIR/$device_name"
    
    echo -e "${BLUE}Testing: $device_name${NC}" | tee -a "$LOG_FILE"
    
    # Check if ground truth exists
    local ground_truth="ground_truth_${device_name}.json"
    if [ ! -f "$ground_truth" ]; then
        echo -e "${YELLOW}Warning: Ground truth file $ground_truth not found. Skipping accuracy validation.${NC}" | tee -a "$LOG_FILE"
        ground_truth=""
    fi
    
    # Run pipeline
    local start_time=$(date +%s)
    
    if [ -n "$ground_truth" ]; then
        uv run pipeline_runner.py \
            --pdf "$doc" \
            --ground_truth "$ground_truth" \
            --output_dir "$result_dir" 2>&1 | tee -a "$LOG_FILE"
    else
        uv run pipeline_runner.py \
            --pdf "$doc" \
            --output_dir "$result_dir" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Check if pipeline completed successfully
    if [ -f "$result_dir/metrics.json" ]; then
        # Extract metrics
        local coverage=$(cat "$result_dir/metrics.json" | jq -r '.quality_metrics.coverage_percent // "N/A"')
        local accuracy=$(cat "$result_dir/metrics.json" | jq -r '.quality_metrics.accuracy_percent // "N/A"')
        local auto_approval=$(cat "$result_dir/metrics.json" | jq -r '.confidence_metrics.auto_approval_rate // "N/A"')
        
        # Store metrics for aggregation
        coverage_scores+=("$coverage")
        accuracy_scores+=("$accuracy")
        auto_approval_scores+=("$auto_approval")
        duration_scores+=("$duration")
        test_names+=("$device_name")
        
        # Determine status
        local status="PASS"
        if [ "$coverage" != "N/A" ] && [ "$(echo "$coverage < 90" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
            status="LOW_COVERAGE"
        elif [ "$accuracy" != "N/A" ] && [ "$(echo "$accuracy < 80" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
            status="LOW_ACCURACY"
        fi
        
        if [ "$status" = "PASS" ]; then
            echo -e "${GREEN}✓ PASS${NC}" | tee -a "$LOG_FILE"
            ((success_count++))
        else
            echo -e "${YELLOW}⚠ $status${NC}" | tee -a "$LOG_FILE"
            ((failure_count++))
        fi
        
        # Add to summary
        echo "$device_name | $coverage% | $accuracy% | $auto_approval% | ${duration}s | $status" >> "$BASELINE_DIR/test_summary.txt"
        
    else
        echo -e "${RED}✗ FAILED - No metrics file generated${NC}" | tee -a "$LOG_FILE"
        ((failure_count++))
        echo "$device_name | FAILED | FAILED | FAILED | ${duration}s | FAILED" >> "$BASELINE_DIR/test_summary.txt"
    fi
    
    echo "" | tee -a "$LOG_FILE"
    ((test_count++))
}

# Function to calculate averages
calculate_averages() {
    local -n array="$1"
    local sum=0
    local count=0
    
    for value in "${array[@]}"; do
        if [ "$value" != "N/A" ] && [ -n "$value" ]; then
            sum=$(echo "$sum + $value" | bc -l 2>/dev/null || echo "0")
            ((count++))
        fi
    done
    
    if [ $count -gt 0 ]; then
        echo "scale=2; $sum / $count" | bc -l 2>/dev/null || echo "0"
    else
        echo "N/A"
    fi
}

# Run tests for all documents
echo "Starting batch test run..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

for doc in "$TEST_DOCS_DIR"/*.pdf; do
    if [ -f "$doc" ]; then
        run_single_test "$doc"
    fi
done

# Calculate and display summary statistics
echo "=== Test Run Summary ===" | tee -a "$LOG_FILE"
echo "Total Tests: $test_count" | tee -a "$LOG_FILE"
echo "Successful: $success_count" | tee -a "$LOG_FILE"
echo "Failed: $failure_count" | tee -a "$LOG_FILE"
echo "Success Rate: $(echo "scale=1; $success_count * 100 / $test_count" | bc -l 2>/dev/null || echo "0")%" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Calculate averages
avg_coverage=$(calculate_averages coverage_scores)
avg_accuracy=$(calculate_averages accuracy_scores)
avg_auto_approval=$(calculate_averages auto_approval_scores)
avg_duration=$(calculate_averages duration_scores)

echo "=== Performance Metrics ===" | tee -a "$LOG_FILE"
echo "Average Coverage: $avg_coverage%" | tee -a "$LOG_FILE"
echo "Average Accuracy: $avg_accuracy%" | tee -a "$LOG_FILE"
echo "Average Auto-Approval Rate: $avg_auto_approval%" | tee -a "$LOG_FILE"
echo "Average Processing Time: $avg_duration seconds" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Add summary to baseline file
echo "" >> "$BASELINE_DIR/test_summary.txt"
echo "=== Summary Statistics ===" >> "$BASELINE_DIR/test_summary.txt"
echo "Total Tests: $test_count" >> "$BASELINE_DIR/test_summary.txt"
echo "Successful: $success_count" >> "$BASELINE_DIR/test_summary.txt"
echo "Failed: $failure_count" >> "$BASELINE_DIR/test_summary.txt"
echo "Success Rate: $(echo "scale=1; $success_count * 100 / $test_count" | bc -l 2>/dev/null || echo "0")%" >> "$BASELINE_DIR/test_summary.txt"
echo "" >> "$BASELINE_DIR/test_summary.txt"
echo "Average Coverage: $avg_coverage%" >> "$BASELINE_DIR/test_summary.txt"
echo "Average Accuracy: $avg_accuracy%" >> "$BASELINE_DIR/test_summary.txt"
echo "Average Auto-Approval Rate: $avg_auto_approval%" >> "$BASELINE_DIR/test_summary.txt"
echo "Average Processing Time: $avg_duration seconds" >> "$BASELINE_DIR/test_summary.txt"

# Generate detailed metrics report
echo "=== Detailed Metrics Report ===" > "$BASELINE_DIR/detailed_metrics.json"
echo "{" >> "$BASELINE_DIR/detailed_metrics.json"
echo "  \"test_run\": {" >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"total_tests\": $test_count," >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"successful_tests\": $success_count," >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"failed_tests\": $failure_count," >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"success_rate\": $(echo "scale=2; $success_count * 100 / $test_count" | bc -l 2>/dev/null || echo "0")" >> "$BASELINE_DIR/detailed_metrics.json"
echo "  }," >> "$BASELINE_DIR/detailed_metrics.json"
echo "  \"performance_metrics\": {" >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"average_coverage\": $avg_coverage," >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"average_accuracy\": $avg_accuracy," >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"average_auto_approval_rate\": $avg_auto_approval," >> "$BASELINE_DIR/detailed_metrics.json"
echo "    \"average_processing_time_seconds\": $avg_duration" >> "$BASELINE_DIR/detailed_metrics.json"
echo "  }," >> "$BASELINE_DIR/detailed_metrics.json"
echo "  \"individual_tests\": [" >> "$BASELINE_DIR/detailed_metrics.json"

# Add individual test results
for i in "${!test_names[@]}"; do
    if [ $i -gt 0 ]; then
        echo "," >> "$BASELINE_DIR/detailed_metrics.json"
    fi
    echo "    {" >> "$BASELINE_DIR/detailed_metrics.json"
    echo "      \"device_name\": \"${test_names[$i]}\"," >> "$BASELINE_DIR/detailed_metrics.json"
    echo "      \"coverage_percent\": ${coverage_scores[$i]}," >> "$BASELINE_DIR/detailed_metrics.json"
    echo "      \"accuracy_percent\": ${accuracy_scores[$i]}," >> "$BASELINE_DIR/detailed_metrics.json"
    echo "      \"auto_approval_rate\": ${auto_approval_scores[$i]}," >> "$BASELINE_DIR/detailed_metrics.json"
    echo "      \"processing_time_seconds\": ${duration_scores[$i]}" >> "$BASELINE_DIR/detailed_metrics.json"
    echo "    }" >> "$BASELINE_DIR/detailed_metrics.json"
done

echo "  ]" >> "$BASELINE_DIR/detailed_metrics.json"
echo "}" >> "$BASELINE_DIR/detailed_metrics.json"

echo "Test run completed: $(date)" | tee -a "$LOG_FILE"
echo "Results saved to: $BASELINE_DIR/" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"

# Exit with appropriate code
if [ $failure_count -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}" | tee -a "$LOG_FILE"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check the log for details.${NC}" | tee -a "$LOG_FILE"
    exit 1
fi 