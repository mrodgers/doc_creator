#!/usr/bin/env python3
"""
AI Documentation Generation Web UI

A minimal Flask-based web interface for the AI-assisted documentation
generation system with confidence visualization and interactive gap reports.
"""

import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

# Import our AI pipeline components
from ai_doc_gen.core.pipeline_orchestrator import PipelineOrchestrator


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle enum serialization."""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

def serialize_pipeline_results(results):
    """Serialize pipeline results, converting enums to strings."""
    if isinstance(results, dict):
        return {k: serialize_pipeline_results(v) for k, v in results.items()}
    elif isinstance(results, list):
        return [serialize_pipeline_results(item) for item in results]
    elif hasattr(results, 'value'):  # Enum
        return results.value
    elif hasattr(results, 'dict'):  # Pydantic model
        return serialize_pipeline_results(results.dict())
    elif hasattr(results, 'model_dump'):  # Pydantic v2 model
        return serialize_pipeline_results(results.model_dump())
    else:
        return results

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

# Global state for pipeline results
pipeline_results = {}

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_document():
    """Handle document upload and processing."""
    if request.method == 'POST':
        if 'document' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{filename}"
            filepath = Path(app.config['UPLOAD_FOLDER']) / safe_filename

            file.save(str(filepath))

            # Process the document
            try:
                result = process_document(str(filepath))
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    return render_template('upload.html')

@app.route('/process/<filename>')
def process_document_route(filename):
    """Process a specific uploaded document."""
    filepath = Path(app.config['UPLOAD_FOLDER']) / filename
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404

    try:
        result = process_document(str(filepath))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<job_id>')
def get_results(job_id):
    """Get processing results for a specific job."""
    if job_id in pipeline_results:
        return jsonify(serialize_pipeline_results(pipeline_results[job_id]))
    return jsonify({'error': 'Job not found'}), 404

@app.route('/visualize/<job_id>')
def visualize_results(job_id):
    """Visualization page for pipeline results."""
    if job_id not in pipeline_results:
        return redirect(url_for('index'))

    return render_template('visualize.html', job_id=job_id, results=serialize_pipeline_results(pipeline_results[job_id]))

@app.route('/export/<job_id>/<format>')
def export_results(job_id, format):
    """Export results in specified format (json, markdown, pdf)."""
    if job_id not in pipeline_results:
        return jsonify({'error': 'Job not found'}), 404

    results = pipeline_results[job_id]

    if format == 'json':
        return jsonify(serialize_pipeline_results(results))
    elif format == 'markdown':
        # Return the generated markdown file if it exists
        output_dir = results.get('output_dir', '')
        if output_dir and Path(output_dir).exists():
            md_file = Path(output_dir) / 'generated_draft.md'
            if md_file.exists():
                return send_file(str(md_file), as_attachment=True, download_name=f'draft_{job_id}.md')
        return jsonify({'error': 'Markdown file not found'}), 404
    elif format == 'pdf':
        # TODO: Implement PDF export
        return jsonify({'error': 'PDF export not yet implemented'}), 501
    else:
        return jsonify({'error': 'Unsupported format'}), 400

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get real-time status of a processing job."""
    if job_id in pipeline_results:
        return jsonify({
            'status': 'completed',
            'results': serialize_pipeline_results(pipeline_results[job_id])
        })
    return jsonify({'status': 'not_found'}), 404

def process_document(filepath: str) -> dict:
    """Process a document through the AI pipeline."""
    # Generate unique job ID
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]

    # Create output directory
    output_dir = Path(app.config['OUTPUT_FOLDER']) / f"job_{job_id}"
    output_dir.mkdir(exist_ok=True)

    try:
        # Initialize pipeline
        config = {
            "llm_provider": "openai",
            "confidence_threshold": 85.0,
            "gap_threshold": 70.0
        }

        orchestrator = PipelineOrchestrator(config=config)

        # Run pipeline asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        pipeline_result = loop.run_until_complete(
            orchestrator.run_pipeline(
                input_files=[filepath],
                output_dir=str(output_dir)
            )
        )

        # Store results
        result = {
            'job_id': job_id,
            'filename': Path(filepath).name,
            'output_dir': str(output_dir),
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'pipeline_results': serialize_pipeline_results(pipeline_result)
        }

        pipeline_results[job_id] = result
        return result

    except Exception as e:
        # Store error results
        error_result = {
            'job_id': job_id,
            'filename': Path(filepath).name,
            'output_dir': str(output_dir),
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        pipeline_results[job_id] = error_result
        raise

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5432)
