#!/usr/bin/env python3
"""
Feedback Collection System

Provides functionality to collect user feedback on generated documentation
and use it for system improvement and learning retention.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class FeedbackType(Enum):
    """Types of feedback that can be collected."""
    QUALITY = "quality"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    USEFULNESS = "usefulness"


class FeedbackRating(Enum):
    """Rating scale for feedback."""
    POOR = 1
    FAIR = 2
    GOOD = 3
    VERY_GOOD = 4
    EXCELLENT = 5


@dataclass
class DocumentFeedback:
    """Feedback for a specific document."""
    document_id: str
    document_name: str
    feedback_type: FeedbackType
    rating: FeedbackRating
    comments: Optional[str] = None
    section_feedback: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class SectionFeedback:
    """Feedback for a specific section of a document."""
    section_name: str
    section_content: str
    rating: FeedbackRating
    comments: Optional[str] = None
    issues_found: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None


class FeedbackCollector:
    """Collects and manages user feedback for system improvement."""
    
    def __init__(self, feedback_dir: str = "feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(exist_ok=True)
        self.feedback_file = self.feedback_dir / "document_feedback.json"
        self.learning_file = self.feedback_dir / "learning_data.json"
        self._load_existing_feedback()
    
    def _load_existing_feedback(self):
        """Load existing feedback data."""
        self.feedback_data = []
        self.learning_data = {}
        
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    self.feedback_data = json.load(f)
            except json.JSONDecodeError:
                self.feedback_data = []
        
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    self.learning_data = json.load(f)
            except json.JSONDecodeError:
                self.learning_data = {}
    
    def _save_feedback(self):
        """Save feedback data to files."""
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=2, default=str)
    
    def _save_learning_data(self):
        """Save learning data to files."""
        with open(self.learning_file, 'w') as f:
            json.dump(self.learning_data, f, indent=2, default=str)
    
    def add_document_feedback(self, feedback: DocumentFeedback):
        """Add feedback for a document."""
        feedback_dict = asdict(feedback)
        self.feedback_data.append(feedback_dict)
        self._save_feedback()
        
        # Update learning data
        self._update_learning_data(feedback)
    
    def _update_learning_data(self, feedback: DocumentFeedback):
        """Update learning data based on feedback."""
        doc_id = feedback.document_id
        
        if doc_id not in self.learning_data:
            self.learning_data[doc_id] = {
                'feedback_count': 0,
                'average_ratings': {},
                'common_issues': [],
                'improvement_suggestions': []
            }
        
        # Update feedback count
        self.learning_data[doc_id]['feedback_count'] += 1
        
        # Update average ratings
        feedback_type = feedback.feedback_type.value
        if feedback_type not in self.learning_data[doc_id]['average_ratings']:
            self.learning_data[doc_id]['average_ratings'][feedback_type] = []
        
        self.learning_data[doc_id]['average_ratings'][feedback_type].append(feedback.rating.value)
        
        # Extract issues and suggestions from comments
        if feedback.comments:
            # Simple keyword-based extraction (could be enhanced with NLP)
            issues_keywords = ['missing', 'incorrect', 'wrong', 'error', 'problem', 'issue']
            suggestions_keywords = ['should', 'could', 'suggest', 'recommend', 'improve']
            
            comment_lower = feedback.comments.lower()
            
            for keyword in issues_keywords:
                if keyword in comment_lower:
                    self.learning_data[doc_id]['common_issues'].append(feedback.comments)
                    break
            
            for keyword in suggestions_keywords:
                if keyword in comment_lower:
                    self.learning_data[doc_id]['improvement_suggestions'].append(feedback.comments)
                    break
        
        self._save_learning_data()
    
    def get_document_feedback(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific document."""
        return [f for f in self.feedback_data if f.get('document_id') == document_id]
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of all feedback."""
        if not self.feedback_data:
            return {
                'total_feedback': 0,
                'average_rating': 0,
                'feedback_by_type': {},
                'recent_feedback': []
            }
        
        # Calculate overall statistics
        total_feedback = len(self.feedback_data)
        all_ratings = []
        for f in self.feedback_data:
            rating = f.get('rating')
            if rating is not None:
                # Handle both enum values and direct integers
                if isinstance(rating, dict) and 'value' in rating:
                    all_ratings.append(rating['value'])
                elif isinstance(rating, int):
                    all_ratings.append(rating)
                elif hasattr(rating, 'value'):
                    all_ratings.append(rating.value)
        
        average_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
        
        # Group by feedback type
        feedback_by_type = {}
        for feedback in self.feedback_data:
            feedback_type = feedback.get('feedback_type', 'unknown')
            if isinstance(feedback_type, dict) and 'value' in feedback_type:
                feedback_type = feedback_type['value']
            elif hasattr(feedback_type, 'value'):
                feedback_type = feedback_type.value
                
            if feedback_type not in feedback_by_type:
                feedback_by_type[feedback_type] = []
            feedback_by_type[feedback_type].append(feedback)
        
        # Get recent feedback (last 10)
        recent_feedback = sorted(
            self.feedback_data, 
            key=lambda x: str(x.get('timestamp', '')), 
            reverse=True
        )[:10]
        
        return {
            'total_feedback': total_feedback,
            'average_rating': average_rating,
            'feedback_by_type': feedback_by_type,
            'recent_feedback': recent_feedback
        }
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning data for system improvement."""
        insights = {
            'document_performance': {},
            'common_issues': [],
            'improvement_areas': [],
            'success_patterns': []
        }
        
        # Analyze document performance
        for doc_id, data in self.learning_data.items():
            if data.get('feedback_count', 0) > 0:
                avg_ratings = data.get('average_ratings', {})
                overall_avg = 0
                rating_count = 0
                
                for feedback_type, ratings in avg_ratings.items():
                    if ratings:
                        overall_avg += sum(ratings) / len(ratings)
                        rating_count += 1
                
                if rating_count > 0:
                    overall_avg /= rating_count
                    
                    insights['document_performance'][doc_id] = {
                        'feedback_count': data.get('feedback_count', 0),
                        'average_rating': overall_avg,
                        'common_issues': data.get('common_issues', []),
                        'improvement_suggestions': data.get('improvement_suggestions', [])
                    }
        
        # Aggregate common issues across documents
        all_issues = []
        for doc_data in insights['document_performance'].values():
            all_issues.extend(doc_data.get('common_issues', []))
        
        insights['common_issues'] = list(set(all_issues))[:10]  # Top 10 unique issues
        
        # Identify improvement areas
        low_performing_docs = [
            doc_id for doc_id, data in insights['document_performance'].items()
            if data.get('average_rating', 0) < 3.0
        ]
        insights['improvement_areas'] = low_performing_docs
        
        # Identify success patterns
        high_performing_docs = [
            doc_id for doc_id, data in insights['document_performance'].items()
            if data.get('average_rating', 0) >= 4.0
        ]
        insights['success_patterns'] = high_performing_docs
        
        return insights
    
    def generate_feedback_html(self, document_id: str, document_name: str) -> str:
        """Generate HTML for embedding feedback collection in documents."""
        html = f"""
        <div class="feedback-widget" style="border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; background-color: #f8f9fa;">
            <h4><i class="fas fa-comment me-2"></i>Document Feedback</h4>
            <p class="text-muted">Help us improve by providing feedback on this document.</p>
            
            <form id="feedback-form-{document_id}" onsubmit="submitFeedback(event, '{document_id}')">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Overall Quality</label>
                            <select class="form-select" name="quality_rating" required>
                                <option value="">Select rating</option>
                                <option value="1">1 - Poor</option>
                                <option value="2">2 - Fair</option>
                                <option value="3">3 - Good</option>
                                <option value="4">4 - Very Good</option>
                                <option value="5">5 - Excellent</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Accuracy</label>
                            <select class="form-select" name="accuracy_rating" required>
                                <option value="">Select rating</option>
                                <option value="1">1 - Poor</option>
                                <option value="2">2 - Fair</option>
                                <option value="3">3 - Good</option>
                                <option value="4">4 - Very Good</option>
                                <option value="5">5 - Excellent</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Completeness</label>
                            <select class="form-select" name="completeness_rating" required>
                                <option value="">Select rating</option>
                                <option value="1">1 - Poor</option>
                                <option value="2">2 - Fair</option>
                                <option value="3">3 - Good</option>
                                <option value="4">4 - Very Good</option>
                                <option value="5">5 - Excellent</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Clarity</label>
                            <select class="form-select" name="clarity_rating" required>
                                <option value="">Select rating</option>
                                <option value="1">1 - Poor</option>
                                <option value="2">2 - Fair</option>
                                <option value="3">3 - Good</option>
                                <option value="4">4 - Very Good</option>
                                <option value="5">5 - Excellent</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Additional Comments</label>
                    <textarea class="form-control" name="comments" rows="3" 
                              placeholder="Please provide any additional feedback, suggestions, or issues you found..."></textarea>
                </div>
                
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-paper-plane me-1"></i>Submit Feedback
                </button>
            </form>
            
            <div id="feedback-success-{document_id}" style="display: none;" class="alert alert-success mt-3">
                <i class="fas fa-check-circle me-2"></i>Thank you for your feedback!
            </div>
        </div>
        
        <script>
        function submitFeedback(event, documentId) {{
            event.preventDefault();
            
            const form = event.target;
            const formData = new FormData(form);
            
            const feedback = {{
                document_id: documentId,
                document_name: '{document_name}',
                quality_rating: parseInt(formData.get('quality_rating')),
                accuracy_rating: parseInt(formData.get('accuracy_rating')),
                completeness_rating: parseInt(formData.get('completeness_rating')),
                clarity_rating: parseInt(formData.get('clarity_rating')),
                comments: formData.get('comments')
            }};
            
            fetch('/api/feedback/submit', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(feedback)
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    document.getElementById(`feedback-success-${{documentId}}`).style.display = 'block';
                    form.style.display = 'none';
                }} else {{
                    alert('Error submitting feedback: ' + data.error);
                }}
            }})
            .catch(error => {{
                alert('Error submitting feedback: ' + error.message);
            }});
        }}
        </script>
        """
        
        return html
    
    def export_feedback_report(self) -> Dict[str, Any]:
        """Export comprehensive feedback report for analysis."""
        summary = self.get_feedback_summary()
        insights = self.get_learning_insights()
        
        return {
            'export_timestamp': datetime.now().isoformat(),
            'feedback_summary': summary,
            'learning_insights': insights,
            'raw_feedback_data': self.feedback_data,
            'learning_data': self.learning_data
        } 