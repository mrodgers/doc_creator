#!/usr/bin/env python3
"""
AI Documentation Generation Web UI

A minimal Flask-based web interface for the AI-assisted documentation
generation system with confidence visualization and interactive gap reports.
"""

import asyncio
import json
import os
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

# Import our AI pipeline components
from ai_doc_gen.core.pipeline_orchestrator import PipelineOrchestrator

# Import gap dashboard components
from ai_doc_gen.ui.gap_dashboard import GapDashboard, GapStatus, create_gap_dashboard_html

# Import feedback collector
from ai_doc_gen.feedback.feedback_collector import FeedbackCollector, DocumentFeedback, FeedbackType, FeedbackRating


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

# Global state for pipeline results and batch processing
pipeline_results = {}
batch_jobs = {}

class BatchJobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BatchJob:
    def __init__(self, batch_id: str, files: List[str]):
        self.batch_id = batch_id
        self.files = files
        self.status = BatchJobStatus.PENDING
        self.progress = 0
        self.total_files = len(files)
        self.completed_files = 0
        self.failed_files = 0
        self.results = {}
        self.errors = {}
        self.start_time = None
        self.end_time = None
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            'batch_id': self.batch_id,
            'status': self.status.value,
            'progress': self.progress,
            'total_files': self.total_files,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'results': self.results,
            'errors': self.errors,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat()
        }

def process_batch_async(batch_id: str):
    """Process batch of documents asynchronously."""
    batch_job = batch_jobs[batch_id]
    batch_job.status = BatchJobStatus.PROCESSING
    batch_job.start_time = datetime.now()
    
    try:
        for i, filepath in enumerate(batch_job.files):
            try:
                # Process individual document
                result = process_document(filepath)
                batch_job.results[Path(filepath).name] = result
                batch_job.completed_files += 1
            except Exception as e:
                batch_job.errors[Path(filepath).name] = str(e)
                batch_job.failed_files += 1
            
            # Update progress
            batch_job.progress = int(((i + 1) / batch_job.total_files) * 100)
            time.sleep(0.1)  # Small delay to allow status updates
        
        batch_job.status = BatchJobStatus.COMPLETED
    except Exception as e:
        batch_job.status = BatchJobStatus.FAILED
        batch_job.errors['batch_error'] = str(e)
    finally:
        batch_job.end_time = datetime.now()

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

@app.route('/batch-upload', methods=['GET', 'POST'])
def batch_upload():
    """Handle multiple document uploads with progress tracking."""
    if request.method == 'POST':
        if 'documents' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400

        files = request.files.getlist('documents')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        # Save uploaded files
        saved_files = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = f"{timestamp}_{filename}"
                filepath = Path(app.config['UPLOAD_FOLDER']) / safe_filename
                file.save(str(filepath))
                saved_files.append(str(filepath))

        if saved_files:
            # Create batch job
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
            batch_job = BatchJob(batch_id, saved_files)
            batch_jobs[batch_id] = batch_job

            # Start processing in background thread
            thread = threading.Thread(target=process_batch_async, args=(batch_id,))
            thread.daemon = True
            thread.start()

            return jsonify({
                'batch_id': batch_id,
                'total_files': len(saved_files),
                'status': 'pending'
            })

    return render_template('batch_upload.html')

@app.route('/api/batch/status/<batch_id>')
def get_batch_status(batch_id):
    """Get real-time batch processing status."""
    if batch_id not in batch_jobs:
        return jsonify({'error': 'Batch job not found'}), 404
    
    return jsonify(batch_jobs[batch_id].to_dict())

@app.route('/api/batch/list')
def list_batch_jobs():
    """List all batch jobs."""
    return jsonify({
        batch_id: job.to_dict() 
        for batch_id, job in batch_jobs.items()
    })

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
        # Generate PDF from results
        try:
            pdf_file = generate_pdf_from_results(results)
            return send_file(pdf_file, as_attachment=True, download_name=f'draft_{job_id}.pdf')
        except Exception as e:
            return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Unsupported format'}), 400

def generate_pdf_from_results(results):
    """Generate PDF from pipeline results."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import tempfile
        
        # Create temporary PDF file
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = pdf_file.name
        pdf_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title = Paragraph("AI-Generated Hardware Documentation", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add metadata
        if 'pipeline_results' in results:
            pipeline_data = results['pipeline_results']
            
            # Add confidence scores
            if 'confidence_scores' in pipeline_data:
                story.append(Paragraph("Confidence Scores", styles['Heading2']))
                for section, score in pipeline_data['confidence_scores'].items():
                    story.append(Paragraph(f"{section}: {score}%", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Add gap analysis
            if 'gap_analysis' in pipeline_data:
                story.append(Paragraph("Gap Analysis", styles['Heading2']))
                for gap in pipeline_data['gap_analysis']:
                    story.append(Paragraph(f"• {gap}", styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        return pdf_path
        
    except ImportError:
        raise Exception("PDF generation requires reportlab library. Install with: pip install reportlab")
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get real-time status of a processing job."""
    if job_id in pipeline_results:
        return jsonify({
            'status': 'completed',
            'results': serialize_pipeline_results(pipeline_results[job_id])
        })
    return jsonify({'status': 'not_found'}), 404

@app.route('/gaps')
def gap_dashboard():
    """Interactive gap analysis dashboard."""
    return render_template('gap_dashboard.html')

@app.route('/api/gaps/<document_name>')
def get_gaps_for_document(document_name):
    """Get gaps for a specific document."""
    try:
        dashboard = GapDashboard(app.config['OUTPUT_FOLDER'])
        gaps = dashboard.get_gaps_for_document(document_name)
        return jsonify(gaps)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gaps/<document_name>/interactive')
def get_interactive_gaps(document_name):
    """Get interactive gap dashboard HTML for a document."""
    try:
        dashboard = GapDashboard(app.config['OUTPUT_FOLDER'])
        gaps = dashboard.get_gaps_for_document(document_name)
        html = create_gap_dashboard_html(gaps)
        return html
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gaps/<gap_id>/status', methods=['POST'])
def update_gap_status(gap_id):
    """Update gap status and collect feedback."""
    try:
        data = request.get_json()
        status = GapStatus(data.get('status', 'open'))
        feedback = data.get('feedback')
        rating = data.get('rating')
        
        dashboard = GapDashboard(app.config['OUTPUT_FOLDER'])
        dashboard.update_gap_status(gap_id, status, feedback, rating)
        
        return jsonify({'success': True, 'message': 'Gap status updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/summary')
def get_feedback_summary():
    """Get summary of document feedback."""
    try:
        feedback_collector = FeedbackCollector()
        summary = feedback_collector.get_feedback_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/insights')
def get_feedback_insights():
    """Get learning insights from feedback."""
    try:
        feedback_collector = FeedbackCollector()
        insights = feedback_collector.get_learning_insights()
        return jsonify(insights)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/export-report')
def export_feedback_report():
    """Export comprehensive feedback report."""
    try:
        feedback_collector = FeedbackCollector()
        report = feedback_collector.export_feedback_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/export')
def export_learning_data():
    """Export learning data for system improvement."""
    try:
        dashboard = GapDashboard(app.config['OUTPUT_FOLDER'])
        learning_data = dashboard.export_learning_data()
        return jsonify(learning_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    """Submit document feedback."""
    try:
        data = request.get_json()
        
        # Create feedback objects for each rating type
        feedback_collector = FeedbackCollector()
        
        # Quality feedback
        if data.get('quality_rating'):
            quality_feedback = DocumentFeedback(
                document_id=data.get('document_id'),
                document_name=data.get('document_name'),
                feedback_type=FeedbackType.QUALITY,
                rating=FeedbackRating(data.get('quality_rating')),
                comments=data.get('comments')
            )
            feedback_collector.add_document_feedback(quality_feedback)
        
        # Accuracy feedback
        if data.get('accuracy_rating'):
            accuracy_feedback = DocumentFeedback(
                document_id=data.get('document_id'),
                document_name=data.get('document_name'),
                feedback_type=FeedbackType.ACCURACY,
                rating=FeedbackRating(data.get('accuracy_rating')),
                comments=data.get('comments')
            )
            feedback_collector.add_document_feedback(accuracy_feedback)
        
        # Completeness feedback
        if data.get('completeness_rating'):
            completeness_feedback = DocumentFeedback(
                document_id=data.get('document_id'),
                document_name=data.get('document_name'),
                feedback_type=FeedbackType.COMPLETENESS,
                rating=FeedbackRating(data.get('completeness_rating')),
                comments=data.get('comments')
            )
            feedback_collector.add_document_feedback(completeness_feedback)
        
        # Clarity feedback
        if data.get('clarity_rating'):
            clarity_feedback = DocumentFeedback(
                document_id=data.get('document_id'),
                document_name=data.get('document_name'),
                feedback_type=FeedbackType.CLARITY,
                rating=FeedbackRating(data.get('clarity_rating')),
                comments=data.get('comments')
            )
            feedback_collector.add_document_feedback(clarity_feedback)
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/system-health')
def system_health():
    """Display system performance metrics and health status."""
    return render_template('system_health.html')

@app.route('/api/system/metrics')
def get_system_metrics():
    """Get real-time system performance metrics."""
    try:
        import psutil
        import os
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_memory_mb = process.memory_info().rss / (1024**2)
        process_cpu_percent = process.cpu_percent()
        
        # System load (Unix-like systems)
        try:
            load_avg = os.getloadavg()
        except AttributeError:
            load_avg = [0, 0, 0]  # Windows doesn't have load average
        
        # Job queue metrics
        active_jobs = len([job for job in batch_jobs.values() if job.status == BatchJobStatus.PROCESSING])
        pending_jobs = len([job for job in batch_jobs.values() if job.status == BatchJobStatus.PENDING])
        completed_jobs = len([job for job in batch_jobs.values() if job.status == BatchJobStatus.COMPLETED])
        failed_jobs = len([job for job in batch_jobs.values() if job.status == BatchJobStatus.FAILED])
        
        # Pipeline results metrics
        total_results = len(pipeline_results)
        successful_results = len([r for r in pipeline_results.values() if r.get('status') == 'completed'])
        error_results = len([r for r in pipeline_results.values() if r.get('status') == 'error'])
        
        # Health status
        health_status = 'healthy'
        if cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
            health_status = 'warning'
        if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
            health_status = 'critical'
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'health_status': health_status,
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'load_average': load_avg
            },
            'memory': {
                'percent': memory_percent,
                'used_gb': round(memory_used_gb, 2),
                'total_gb': round(memory_total_gb, 2)
            },
            'disk': {
                'percent': disk_percent,
                'used_gb': round(disk_used_gb, 2),
                'total_gb': round(disk_total_gb, 2)
            },
            'process': {
                'memory_mb': round(process_memory_mb, 2),
                'cpu_percent': process_cpu_percent
            },
            'jobs': {
                'active': active_jobs,
                'pending': pending_jobs,
                'completed': completed_jobs,
                'failed': failed_jobs,
                'total': len(batch_jobs)
            },
            'pipeline': {
                'total_results': total_results,
                'successful': successful_results,
                'errors': error_results,
                'success_rate': round((successful_results / total_results * 100) if total_results > 0 else 0, 2)
            }
        })
    except ImportError:
        return jsonify({
            'error': 'psutil library not available. Install with: pip install psutil',
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'Failed to get system metrics: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/system/health')
def get_system_health():
    """Get system health status."""
    try:
        import psutil
        
        # Basic health checks
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Determine overall health
        if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
            status = 'critical'
        elif cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
            status = 'warning'
        else:
            status = 'healthy'
        
        return jsonify({
            'status': status,
            'checks': {
                'cpu': {'status': 'healthy' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'},
                'memory': {'status': 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 95 else 'critical'},
                'disk': {'status': 'healthy' if disk_percent < 90 else 'warning' if disk_percent < 95 else 'critical'}
            },
            'timestamp': datetime.now().isoformat()
        })
    except ImportError:
        return jsonify({
            'status': 'unknown',
            'error': 'psutil library not available',
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

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
    port = int(os.getenv('WEB_PORT', 5476))
    app.run(debug=True, host='0.0.0.0', port=port)
