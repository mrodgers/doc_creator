#!/usr/bin/env python3
"""
Interactive Gap Analysis Dashboard

Provides an interactive interface for viewing, managing, and providing feedback on
documentation gaps identified by the AI system.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class GapSeverity(Enum):
    """Gap severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GapStatus(Enum):
    """Gap resolution status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class GapItem:
    """Individual gap item with feedback capabilities."""
    id: str
    title: str
    description: str
    severity: GapSeverity
    confidence: float
    source_section: str
    suggested_resolution: str
    status: GapStatus = GapStatus.OPEN
    user_feedback: Optional[str] = None
    feedback_rating: Optional[int] = None  # 1-5 scale
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class GapDashboard:
    """Interactive gap analysis dashboard with feedback collection."""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.gaps_file = self.output_dir / "gap_feedback.json"
        self.feedback_file = self.output_dir / "user_feedback.json"
        self._load_existing_feedback()
    
    def _load_existing_feedback(self):
        """Load existing gap feedback and user feedback."""
        self.gap_feedback = {}
        self.user_feedback = {}
        
        if self.gaps_file.exists():
            try:
                with open(self.gaps_file, 'r') as f:
                    self.gap_feedback = json.load(f)
            except json.JSONDecodeError:
                self.gap_feedback = {}
        
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    self.user_feedback = json.load(f)
            except json.JSONDecodeError:
                self.user_feedback = {}
    
    def _save_feedback(self):
        """Save feedback data to files."""
        self.output_dir.mkdir(exist_ok=True)
        
        with open(self.gaps_file, 'w') as f:
            json.dump(self.gap_feedback, f, indent=2, default=str)
        
        with open(self.feedback_file, 'w') as f:
            json.dump(self.user_feedback, f, indent=2, default=str)
    
    def parse_gap_report(self, gap_report_path: str) -> List[GapItem]:
        """Parse a gap report and convert to interactive gap items."""
        gap_items = []
        
        if not Path(gap_report_path).exists():
            return gap_items
        
        try:
            with open(gap_report_path, 'r') as f:
                content = f.read()
            
            # Parse markdown gap report
            sections = content.split('## ')
            
            for section in sections[1:]:  # Skip first empty section
                lines = section.strip().split('\n')
                if not lines:
                    continue
                
                title = lines[0].strip()
                if not title or 'gap' not in title.lower():
                    continue
                
                # Extract gap details
                description = ""
                severity = GapSeverity.MEDIUM
                confidence = 0.0
                source_section = ""
                suggested_resolution = ""
                
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith('- **Description:**'):
                        description = line.replace('- **Description:**', '').strip()
                    elif line.startswith('- **Severity:**'):
                        severity_str = line.replace('- **Severity:**', '').strip().lower()
                        severity = GapSeverity(severity_str) if severity_str in [s.value for s in GapSeverity] else GapSeverity.MEDIUM
                    elif line.startswith('- **Confidence:**'):
                        try:
                            confidence = float(line.replace('- **Confidence:**', '').replace('%', '').strip())
                        except ValueError:
                            confidence = 0.0
                    elif line.startswith('- **Source Section:**'):
                        source_section = line.replace('- **Source Section:**', '').strip()
                    elif line.startswith('- **Suggested Resolution:**'):
                        suggested_resolution = line.replace('- **Suggested Resolution:**', '').strip()
                
                if description:  # Only add if we have a description
                    gap_id = f"{Path(gap_report_path).stem}_{len(gap_items)}"
                    gap_item = GapItem(
                        id=gap_id,
                        title=title,
                        description=description,
                        severity=severity,
                        confidence=confidence,
                        source_section=source_section,
                        suggested_resolution=suggested_resolution
                    )
                    gap_items.append(gap_item)
        
        except Exception as e:
            print(f"Error parsing gap report {gap_report_path}: {e}")
        
        return gap_items
    
    def get_gaps_for_document(self, document_name: str) -> List[Dict[str, Any]]:
        """Get all gaps for a specific document with feedback."""
        gaps = []
        
        # Find gap report for this document
        for output_dir in self.output_dir.glob(f"*{document_name}*"):
            gap_report = output_dir / "gap_report.md"
            if gap_report.exists():
                gap_items = self.parse_gap_report(str(gap_report))
                
                for item in gap_items:
                    gap_data = asdict(item)
                    
                    # Add existing feedback if available
                    if item.id in self.gap_feedback:
                        gap_data.update(self.gap_feedback[item.id])
                    
                    gaps.append(gap_data)
        
        return gaps
    
    def update_gap_status(self, gap_id: str, status: GapStatus, feedback: str = None, rating: int = None):
        """Update gap status and collect user feedback."""
        if gap_id not in self.gap_feedback:
            self.gap_feedback[gap_id] = {}
        
        self.gap_feedback[gap_id].update({
            'status': status.value,
            'user_feedback': feedback,
            'feedback_rating': rating,
            'updated_at': datetime.now().isoformat()
        })
        
        self._save_feedback()
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of user feedback for learning retention."""
        total_gaps = len(self.gap_feedback)
        resolved_gaps = sum(1 for gap in self.gap_feedback.values() if gap.get('status') == GapStatus.RESOLVED.value)
        ignored_gaps = sum(1 for gap in self.gap_feedback.values() if gap.get('status') == GapStatus.IGNORED.value)
        
        ratings = [gap.get('feedback_rating') for gap in self.gap_feedback.values() if gap.get('feedback_rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            'total_gaps': total_gaps,
            'resolved_gaps': resolved_gaps,
            'ignored_gaps': ignored_gaps,
            'resolution_rate': (resolved_gaps / total_gaps * 100) if total_gaps > 0 else 0,
            'average_rating': avg_rating,
            'feedback_count': len(ratings)
        }
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for system improvement."""
        learning_data = {
            'gap_patterns': {},
            'user_preferences': {},
            'resolution_effectiveness': {},
            'feedback_insights': []
        }
        
        # Analyze gap patterns
        for gap_id, feedback in self.gap_feedback.items():
            if 'user_feedback' in feedback and feedback['user_feedback']:
                learning_data['feedback_insights'].append({
                    'gap_id': gap_id,
                    'feedback': feedback['user_feedback'],
                    'rating': feedback.get('feedback_rating'),
                    'status': feedback.get('status'),
                    'timestamp': feedback.get('updated_at')
                })
        
        return learning_data


def create_gap_dashboard_html(gaps: List[Dict[str, Any]]) -> str:
    """Generate HTML for interactive gap dashboard."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interactive Gap Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .gap-card { margin-bottom: 1rem; }
            .severity-critical { border-left: 4px solid #dc3545; }
            .severity-high { border-left: 4px solid #fd7e14; }
            .severity-medium { border-left: 4px solid #ffc107; }
            .severity-low { border-left: 4px solid #28a745; }
            .status-open { background-color: #f8f9fa; }
            .status-in-progress { background-color: #e3f2fd; }
            .status-resolved { background-color: #e8f5e8; }
            .status-ignored { background-color: #f5f5f5; }
            .feedback-form { display: none; }
        </style>
    </head>
    <body>
        <div class="container-fluid mt-4">
            <h1><i class="fas fa-exclamation-triangle me-2"></i>Interactive Gap Dashboard</h1>
            
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Total Gaps</h5>
                            <h2 class="text-primary">{total_gaps}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Critical</h5>
                            <h2 class="text-danger">{critical_count}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Resolved</h5>
                            <h2 class="text-success">{resolved_count}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Avg Rating</h5>
                            <h2 class="text-warning">{avg_rating:.1f}</h2>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-list me-2"></i>Gap Analysis</h5>
                        </div>
                        <div class="card-body">
    """
    
    # Calculate summary stats
    total_gaps = len(gaps)
    critical_count = sum(1 for gap in gaps if gap.get('severity') == 'critical')
    resolved_count = sum(1 for gap in gaps if gap.get('status') == 'resolved')
    ratings = [gap.get('feedback_rating') for gap in gaps if gap.get('feedback_rating')]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    html = html.format(
        total_gaps=total_gaps,
        critical_count=critical_count,
        resolved_count=resolved_count,
        avg_rating=avg_rating
    )
    
    # Generate gap cards
    for gap in gaps:
        severity_class = f"severity-{gap.get('severity', 'medium')}"
        status_class = f"status-{gap.get('status', 'open')}"
        
        html += f"""
            <div class="card gap-card {severity_class} {status_class}">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <h5 class="card-title">{gap.get('title', 'Untitled Gap')}</h5>
                            <p class="card-text">{gap.get('description', 'No description')}</p>
                            <div class="row">
                                <div class="col-md-3">
                                    <small class="text-muted">
                                        <i class="fas fa-exclamation-circle me-1"></i>
                                        Severity: {gap.get('severity', 'medium').title()}
                                    </small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted">
                                        <i class="fas fa-percentage me-1"></i>
                                        Confidence: {gap.get('confidence', 0):.1f}%
                                    </small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted">
                                        <i class="fas fa-file-alt me-1"></i>
                                        Source: {gap.get('source_section', 'Unknown')}
                                    </small>
                                </div>
                                <div class="col-md-3">
                                    <small class="text-muted">
                                        <i class="fas fa-clock me-1"></i>
                                        Status: {gap.get('status', 'open').replace('_', ' ').title()}
                                    </small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="d-grid gap-2">
                                <button class="btn btn-sm btn-outline-primary" onclick="showFeedback('{gap.get('id')}')">
                                    <i class="fas fa-comment me-1"></i>Provide Feedback
                                </button>
                                <button class="btn btn-sm btn-outline-success" onclick="updateStatus('{gap.get('id')}', 'resolved')">
                                    <i class="fas fa-check me-1"></i>Mark Resolved
                                </button>
                                <button class="btn btn-sm btn-outline-secondary" onclick="updateStatus('{gap.get('id')}', 'ignored')">
                                    <i class="fas fa-times me-1"></i>Ignore
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div id="feedback-{gap.get('id')}" class="feedback-form mt-3">
                        <div class="card">
                            <div class="card-body">
                                <h6>Provide Feedback</h6>
                                <div class="mb-3">
                                    <label class="form-label">Rating (1-5):</label>
                                    <select class="form-select" id="rating-{gap.get('id')}">
                                        <option value="">Select rating</option>
                                        <option value="1">1 - Poor</option>
                                        <option value="2">2 - Fair</option>
                                        <option value="3">3 - Good</option>
                                        <option value="4">4 - Very Good</option>
                                        <option value="5">5 - Excellent</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Comments:</label>
                                    <textarea class="form-control" id="feedback-text-{gap.get('id')}" rows="3" placeholder="Provide detailed feedback about this gap..."></textarea>
                                </div>
                                <button class="btn btn-primary" onclick="submitFeedback('{gap.get('id')}')">
                                    <i class="fas fa-save me-1"></i>Submit Feedback
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """
    
    html += """
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function showFeedback(gapId) {
                const feedbackForm = document.getElementById(`feedback-${gapId}`);
                feedbackForm.style.display = feedbackForm.style.display === 'none' ? 'block' : 'none';
            }
            
            function updateStatus(gapId, status) {
                // In a real implementation, this would make an API call
                console.log(`Updating gap ${gapId} to status: ${status}`);
                alert(`Gap status updated to: ${status}`);
                location.reload();
            }
            
            function submitFeedback(gapId) {
                const rating = document.getElementById(`rating-${gapId}`).value;
                const feedback = document.getElementById(`feedback-text-${gapId}`).value;
                
                if (!rating) {
                    alert('Please select a rating');
                    return;
                }
                
                // In a real implementation, this would make an API call
                console.log(`Submitting feedback for gap ${gapId}:`, { rating, feedback });
                alert('Feedback submitted successfully!');
                location.reload();
            }
        </script>
    </body>
    </html>
    """
    
    return html 