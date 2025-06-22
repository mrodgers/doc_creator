#!/bin/bash
# performance_dashboard.sh - Real-time performance monitoring and analysis

# Configuration
RESULTS_DIR="test_results"
BASELINE_DIR="baseline_metrics"
DASHBOARD_FILE="performance_dashboard.html"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if jq is available
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed.${NC}"
        echo "Please install jq: brew install jq (macOS) or apt-get install jq (Ubuntu)"
        exit 1
    fi
    
    if ! command -v bc &> /dev/null; then
        echo -e "${RED}Error: bc is required but not installed.${NC}"
        echo "Please install bc: brew install bc (macOS) or apt-get install bc (Ubuntu)"
        exit 1
    fi
}

# Function to generate HTML dashboard
generate_html_dashboard() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    cat > "$DASHBOARD_FILE" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hardware Specification Extraction Pipeline - Performance Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .metric-card h3 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 1.1em;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .status-excellent { color: #28a745; }
        .status-good { color: #ffc107; }
        .status-poor { color: #dc3545; }
        .results-table {
            margin: 30px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .results-table h3 {
            margin: 0;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
        .chart-container {
            margin: 30px;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .chart-container h3 {
            margin: 0 0 20px 0;
            color: #333;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }
        .progress-fill.warning {
            background: linear-gradient(90deg, #ffc107, #fd7e14);
        }
        .progress-fill.danger {
            background: linear-gradient(90deg, #dc3545, #e83e8c);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Performance Dashboard</h1>
            <p>Hardware Specification Extraction Pipeline - Last Updated: $timestamp</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Average Coverage</h3>
                <div class="metric-value status-$(get_status_class "$avg_coverage" 95 85)">$avg_coverage%</div>
                <div class="metric-label">Target: >95%</div>
                <div class="progress-bar">
                    <div class="progress-fill $(get_progress_class "$avg_coverage" 95 85)" style="width: $(echo "scale=1; $avg_coverage" | bc -l)%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Average Accuracy</h3>
                <div class="metric-value status-$(get_status_class "$avg_accuracy" 90 80)">$avg_accuracy%</div>
                <div class="metric-label">Target: >90%</div>
                <div class="progress-bar">
                    <div class="progress-fill $(get_progress_class "$avg_accuracy" 90 80)" style="width: $(echo "scale=1; $avg_accuracy" | bc -l)%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Auto-Approval Rate</h3>
                <div class="metric-value status-$(get_status_class "$avg_auto_approval" 90 85)">$avg_auto_approval%</div>
                <div class="metric-label">Target: >90%</div>
                <div class="progress-bar">
                    <div class="progress-fill $(get_progress_class "$avg_auto_approval" 90 85)" style="width: $(echo "scale=1; $avg_auto_approval" | bc -l)%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Processing Time</h3>
                <div class="metric-value status-$(get_status_class_reverse "$avg_duration" 30 60)">${avg_duration}s</div>
                <div class="metric-label">Target: <30s</div>
                <div class="progress-bar">
                    <div class="progress-fill $(get_progress_class_reverse "$avg_duration" 30 60)" style="width: $(echo "scale=1; 100 - ($avg_duration * 100 / 60)" | bc -l)%"></div>
                </div>
            </div>
        </div>
        
        <div class="results-table">
            <h3>Individual Test Results</h3>
            <table>
                <thead>
                    <tr>
                        <th>Device Name</th>
                        <th>Coverage</th>
                        <th>Accuracy</th>
                        <th>Auto-Approval</th>
                        <th>Duration</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
EOF

    # Add table rows for each test result
    if [ -f "$BASELINE_DIR/test_summary.txt" ]; then
        # Skip header lines and add data rows
        tail -n +6 "$BASELINE_DIR/test_summary.txt" | grep -v "^===" | grep -v "^$" | while IFS='|' read -r device coverage accuracy auto_approval duration status; do
            # Clean up whitespace
            device=$(echo "$device" | xargs)
            coverage=$(echo "$coverage" | xargs)
            accuracy=$(echo "$accuracy" | xargs)
            auto_approval=$(echo "$auto_approval" | xargs)
            duration=$(echo "$duration" | xargs)
            status=$(echo "$status" | xargs)
            
            # Determine status class
            status_class=""
            case "$status" in
                "PASS") status_class="status-excellent" ;;
                "LOW_COVERAGE"|"LOW_ACCURACY") status_class="status-good" ;;
                "FAILED") status_class="status-poor" ;;
            esac
            
            echo "                    <tr>"
            echo "                        <td>$device</td>"
            echo "                        <td>$coverage</td>"
            echo "                        <td>$accuracy</td>"
            echo "                        <td>$auto_approval</td>"
            echo "                        <td>${duration}s</td>"
            echo "                        <td class=\"$status_class\">$status</td>"
            echo "                    </tr>"
        done >> "$DASHBOARD_FILE"
    fi

    cat >> "$DASHBOARD_FILE" << EOF
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by Hardware Specification Extraction Pipeline Performance Dashboard</p>
            <p>Refresh this page to see updated metrics</p>
        </div>
    </div>
</body>
</html>
EOF
}

# Function to get status class based on value and thresholds
get_status_class() {
    local value="$1"
    local excellent_threshold="$2"
    local good_threshold="$3"
    
    if [ "$value" = "N/A" ] || [ -z "$value" ]; then
        echo "poor"
    elif [ "$(echo "$value >= $excellent_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "excellent"
    elif [ "$(echo "$value >= $good_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "good"
    else
        echo "poor"
    fi
}

# Function to get status class for reverse metrics (lower is better)
get_status_class_reverse() {
    local value="$1"
    local excellent_threshold="$2"
    local good_threshold="$3"
    
    if [ "$value" = "N/A" ] || [ -z "$value" ]; then
        echo "poor"
    elif [ "$(echo "$value <= $excellent_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "excellent"
    elif [ "$(echo "$value <= $good_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "good"
    else
        echo "poor"
    fi
}

# Function to get progress bar class
get_progress_class() {
    local value="$1"
    local excellent_threshold="$2"
    local good_threshold="$3"
    
    if [ "$value" = "N/A" ] || [ -z "$value" ]; then
        echo "danger"
    elif [ "$(echo "$value >= $excellent_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo ""
    elif [ "$(echo "$value >= $good_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "warning"
    else
        echo "danger"
    fi
}

# Function to get progress bar class for reverse metrics
get_progress_class_reverse() {
    local value="$1"
    local excellent_threshold="$2"
    local good_threshold="$3"
    
    if [ "$value" = "N/A" ] || [ -z "$value" ]; then
        echo "danger"
    elif [ "$(echo "$value <= $excellent_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo ""
    elif [ "$(echo "$value <= $good_threshold" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "warning"
    else
        echo "danger"
    fi
}

# Function to calculate averages from metrics files
calculate_averages() {
    local sum=0
    local count=0
    
    for metrics_file in "$RESULTS_DIR"/*/metrics.json; do
        if [ -f "$metrics_file" ]; then
            local value=$(jq -r "$1" "$metrics_file" 2>/dev/null)
            if [ "$value" != "null" ] && [ "$value" != "N/A" ] && [ -n "$value" ]; then
                sum=$(echo "$sum + $value" | bc -l 2>/dev/null || echo "0")
                ((count++))
            fi
        fi
    done
    
    if [ $count -gt 0 ]; then
        echo "scale=2; $sum / $count" | bc -l 2>/dev/null || echo "0"
    else
        echo "N/A"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}=== Performance Dashboard ===${NC}"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Check if results directory exists
    if [ ! -d "$RESULTS_DIR" ]; then
        echo -e "${RED}Error: Results directory $RESULTS_DIR not found.${NC}"
        echo "Please run tests first using test_runner.sh"
        exit 1
    fi
    
    # Calculate averages
    echo -e "${CYAN}Calculating performance metrics...${NC}"
    avg_coverage=$(calculate_averages '.quality_metrics.coverage_percent')
    avg_accuracy=$(calculate_averages '.quality_metrics.accuracy_percent')
    avg_auto_approval=$(calculate_averages '.confidence_metrics.auto_approval_rate')
    avg_duration=$(calculate_averages '.pipeline_run.duration_seconds')
    
    echo ""
    echo -e "${GREEN}📊 Overall Performance:${NC}"
    echo "Average Coverage: $avg_coverage%"
    echo "Average Accuracy: $avg_accuracy%"
    echo "Average Auto-Approval Rate: $avg_auto_approval%"
    echo "Average Processing Time: $avg_duration seconds"
    echo ""
    
    # Generate confidence distribution analysis
    echo -e "${PURPLE}📈 Confidence Distribution:${NC}"
    if command -v jq &> /dev/null; then
        jq -s '
            map(.confidence_metrics.confidence_distribution) | 
            reduce .[] as $item ({}; 
                to_entries | .[] | .key as $k | .value as $v | 
                .[$k] = (.[$k] // 0) + $v
            )
        ' "$RESULTS_DIR"/*/metrics.json 2>/dev/null || echo "No confidence data available"
    fi
    echo ""
    
    # Generate HTML dashboard
    echo -e "${CYAN}Generating HTML dashboard...${NC}"
    generate_html_dashboard
    
    echo -e "${GREEN}✅ Dashboard generated successfully!${NC}"
    echo "HTML Dashboard: $DASHBOARD_FILE"
    echo ""
    
    # Open dashboard in browser if possible
    if command -v open &> /dev/null; then
        echo -e "${BLUE}Opening dashboard in browser...${NC}"
        open "$DASHBOARD_FILE"
    elif command -v xdg-open &> /dev/null; then
        echo -e "${BLUE}Opening dashboard in browser...${NC}"
        xdg-open "$DASHBOARD_FILE"
    else
        echo -e "${YELLOW}Please open $DASHBOARD_FILE in your web browser to view the dashboard.${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Performance dashboard completed!${NC}"
}

# Run main function
main "$@" 