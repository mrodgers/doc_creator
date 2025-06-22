# pipeline_runner.py
"""
End-to-End Pipeline Runner

Orchestrates the full workflow:
  1. Chapter Extraction
  2. Spec Extraction
  3. Template Generation
  4. Markdown Rendering
  5. Quality Validation

Usage:
    python pipeline_runner.py \
      --pdf path/to/guide.pdf \
      --ground_truth path/to/ground_truth_specs.json \
      --output_dir path/to/output_dir

Ensure all required scripts and configs are in the same directory:
  - extract_chapter1.py
  - spec_extractor.py
  - template_generator.py
  - markdown_renderer.py
  - quality_validation.py
  - template_rules.yaml

The runner assumes extract_chapter1.py accepts a `--pdf` argument to specify the input PDF.
"""
import argparse
import subprocess
import sys
import os
import shutil
import json
import datetime
import time
from pathlib import Path

def run_step(cmd, step_name):
    print(f"=== Running {step_name} ===")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during {step_name}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="End-to-end pipeline runner")
    parser.add_argument("--pdf", required=True, help="Path to input PDF file")
    parser.add_argument("--ground_truth", required=True,
                        help="Path to ground truth specs JSON")
    parser.add_argument("--output_dir", default="pipeline_output",
                        help="Directory where outputs will be stored")
    args = parser.parse_args()

    pdf_path = os.path.abspath(args.pdf)
    ground_truth = os.path.abspath(args.ground_truth)
    out_dir = os.path.abspath(args.output_dir)

    # Record start time for metrics
    start_time = time.time()

    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)

    # Store original working directory
    original_dir = os.getcwd()
    
    # Change to output directory for all operations
    os.chdir(out_dir)

    # Copy required configuration files to output directory
    config_files = ['template_rules.yaml']
    for config_file in config_files:
        src_path = os.path.join(original_dir, config_file)
        if os.path.exists(src_path):
            shutil.copy2(src_path, config_file)
            print(f"Copied {config_file} to output directory")
        else:
            print(f"Warning: {config_file} not found in {original_dir}")

    # 1. Chapter Extraction
    run_step([
        "uv", "run", os.path.join(original_dir, "extract_chapter1.py"),
        "--pdf", pdf_path
    ], "Chapter Extraction")

    # Step 2: Extract specifications with confidence scoring
    print("=== Running Spec Extraction with Confidence Scoring ===")
    try:
        subprocess.run([
            "uv", "run", os.path.join(original_dir, "spec_extractor.py")
        ], check=True)
        print("✅ Spec extraction with confidence scoring complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Spec Extraction: {e}")
        return
    
    # Step 3: Run audit only on low-confidence specs (if any)
    print("=== Running Audit on Low-Confidence Specs ===")
    try:
        # Check if there are specs requiring review
        with open("extracted_specs_triage.json", "r") as f:
            triage_results = json.load(f)
        
        review_needed = triage_results.get('review', [])
        if review_needed:
            print(f"Found {len(review_needed)} specs requiring audit...")
            subprocess.run([
                "uv", "run", os.path.join(original_dir, "audit_specs.py")
            ], check=True)
            print("✅ Audit complete")
        else:
            print("✅ No specs require auditing - all specs have high confidence!")
            # Copy extracted specs as corrected specs
            with open("extracted_specs.json", "r") as f:
                extracted_specs = json.load(f)
            with open("corrected_specs.json", "w") as f:
                json.dump(extracted_specs, f, indent=2)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Audit: {e}")
        return
    except FileNotFoundError:
        print("No triage results found, skipping audit...")
        # Copy extracted specs as corrected specs
        with open("extracted_specs.json", "r") as f:
            extracted_specs = json.load(f)
        with open("corrected_specs.json", "w") as f:
            json.dump(extracted_specs, f, indent=2)

    # 3. Template Generation
    run_step([
        "uv", "run", os.path.join(original_dir, "template_generator.py")
    ], "Template Generation")

    # 4. Markdown Rendering
    md_out = os.path.join(out_dir, "chapter1.md")
    run_step([
        "uv", "run", os.path.join(original_dir, "markdown_renderer.py"),
        "chapter1_template.json", "-o", md_out
    ], "Markdown Rendering")

    # 5. Quality Validation
    run_step([
        "uv", "run", os.path.join(original_dir, "quality_validation.py"),
        "--extracted", "extracted_specs.json",
        "--ground", ground_truth
    ], "Quality Validation")

    # 6. Collect and save metrics
    print("=== Collecting Pipeline Metrics ===")
    metrics = collect_metrics(original_dir, out_dir, start_time, pdf_path, ground_truth)
    
    # Save metrics to file
    metrics_path = os.path.join(out_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print("\n=== Pipeline Metrics Summary ===")
    print(f"Duration: {metrics['pipeline_run']['duration_seconds']} seconds")
    print(f"Total Specs: {metrics['extraction_metrics'].get('total_specs_extracted', 'N/A')}")
    print(f"Auto-Approval Rate: {metrics['confidence_metrics'].get('auto_approval_rate', 'N/A')}%")
    print(f"Review Rate: {metrics['confidence_metrics'].get('review_rate', 'N/A')}%")
    print(f"Average Confidence: {metrics['confidence_metrics'].get('average_confidence', 'N/A')}%")
    print(f"Final Accuracy: {metrics['quality_metrics'].get('accuracy_percent', 'N/A')}%")
    print(f"Coverage: {metrics['quality_metrics'].get('coverage_percent', 'N/A')}%")
    print(f"Metrics saved to: {metrics_path}")

    print("\n=== Pipeline Completed Successfully ===")

def collect_metrics(original_dir, out_dir, start_time, pdf_path, ground_truth_path):
    """Collect comprehensive metrics from the pipeline run."""
    
    end_time = time.time()
    duration = end_time - start_time
    
    metrics = {
        "pipeline_run": {
            "timestamp": datetime.datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "pdf_source": os.path.basename(pdf_path),
            "ground_truth_source": os.path.basename(ground_truth_path),
            "output_directory": out_dir
        },
        "extraction_metrics": {},
        "confidence_metrics": {},
        "audit_metrics": {},
        "template_metrics": {},
        "quality_metrics": {},
        "file_outputs": {}
    }
    
    # Collect extraction metrics
    try:
        with open(os.path.join(out_dir, "extracted_specs.json"), "r") as f:
            extracted_specs = json.load(f)
        metrics["extraction_metrics"] = {
            "total_specs_extracted": len(extracted_specs),
            "specs_with_values": len([s for s in extracted_specs if s.get("value", "").strip()]),
            "empty_specs": len([s for s in extracted_specs if not s.get("value", "").strip()])
        }
    except FileNotFoundError:
        metrics["extraction_metrics"] = {"error": "extracted_specs.json not found"}
    
    # Collect confidence metrics
    try:
        with open(os.path.join(out_dir, "extracted_specs_triage.json"), "r") as f:
            triage_results = json.load(f)
        
        confidences = [spec.get("confidence", 100) for spec in extracted_specs]
        metrics["confidence_metrics"] = {
            "threshold": triage_results.get("threshold", 90),
            "total_specs": triage_results.get("total_specs", 0),
            "auto_approved": triage_results.get("auto_approved", 0),
            "review_needed": triage_results.get("review_needed", 0),
            "auto_approval_rate": round(triage_results.get("auto_approved", 0) / max(triage_results.get("total_specs", 1), 1) * 100, 2),
            "review_rate": round(triage_results.get("review_needed", 0) / max(triage_results.get("total_specs", 1), 1) * 100, 2),
            "average_confidence": round(sum(confidences) / len(confidences), 2) if confidences else 0,
            "min_confidence": min(confidences) if confidences else 0,
            "max_confidence": max(confidences) if confidences else 0,
            "confidence_distribution": {
                "90-100": len([c for c in confidences if 90 <= c <= 100]),
                "70-89": len([c for c in confidences if 70 <= c < 90]),
                "50-69": len([c for c in confidences if 50 <= c < 70]),
                "30-49": len([c for c in confidences if 30 <= c < 50]),
                "0-29": len([c for c in confidences if 0 <= c < 30])
            }
        }
    except FileNotFoundError:
        metrics["confidence_metrics"] = {"error": "extracted_specs_triage.json not found"}
    
    # Collect audit metrics
    try:
        with open(os.path.join(out_dir, "corrected_specs.json"), "r") as f:
            corrected_specs = json.load(f)
        
        # Count specs that were audited (confidence boosted to 95)
        audited_specs = [s for s in corrected_specs if s.get("confidence") == 95]
        metrics["audit_metrics"] = {
            "specs_audited": len(audited_specs),
            "audit_rate": round(len(audited_specs) / max(len(corrected_specs), 1) * 100, 2),
            "audited_spec_items": [s["spec_item"] for s in audited_specs]
        }
    except FileNotFoundError:
        metrics["audit_metrics"] = {"error": "corrected_specs.json not found"}
    
    # Collect template metrics
    try:
        with open(os.path.join(out_dir, "chapter1_template.json"), "r") as f:
            template_data = json.load(f)
        
        # Count template placeholders
        template_text = json.dumps(template_data)
        placeholder_count = template_text.count("{{")
        
        metrics["template_metrics"] = {
            "template_placeholders": placeholder_count,
            "template_size_bytes": len(template_text)
        }
    except FileNotFoundError:
        metrics["template_metrics"] = {"error": "chapter1_template.json not found"}
    
    # Collect quality metrics
    try:
        # Run quality validation and capture output
        result = subprocess.run([
            "uv", "run", os.path.join(original_dir, "quality_validation.py"),
            "--extracted", "corrected_specs.json",
            "--ground", ground_truth_path
        ], capture_output=True, text=True, cwd=out_dir)
        
        # Parse quality validation output
        output_lines = result.stdout.split('\n')
        quality_metrics = {}
        for line in output_lines:
            if "Total ground-truth specs" in line:
                quality_metrics["ground_truth_specs"] = int(line.split(':')[1].strip())
            elif "Total extracted specs" in line:
                quality_metrics["extracted_specs"] = int(line.split(':')[1].strip())
            elif "Matched specs" in line:
                quality_metrics["matched_specs"] = int(line.split(':')[1].strip())
            elif "Coverage" in line:
                quality_metrics["coverage_percent"] = float(line.split(':')[1].strip().replace('%', ''))
            elif "Accuracy" in line:
                quality_metrics["accuracy_percent"] = float(line.split(':')[1].strip().replace('%', ''))
        
        metrics["quality_metrics"] = quality_metrics
    except Exception as e:
        metrics["quality_metrics"] = {"error": str(e)}
    
    # Collect file outputs
    output_files = []
    for file_path in Path(out_dir).rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(out_dir)
            output_files.append({
                "filename": str(rel_path),
                "size_bytes": file_path.stat().st_size,
                "modified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    
    metrics["file_outputs"] = {
        "total_files": len(output_files),
        "files": output_files
    }
    
    return metrics

if __name__ == '__main__':
    main()
