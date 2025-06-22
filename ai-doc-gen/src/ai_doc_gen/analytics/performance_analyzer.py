"""
Advanced Performance Analyzer

This module provides comprehensive analytics and performance insights for the
document processing system, including metrics, trends, and optimization recommendations.
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingStats:
    """Statistics for document processing."""
    total_documents: int
    successful_documents: int
    failed_documents: int
    average_processing_time: float
    total_processing_time: float
    fastest_processing_time: float
    slowest_processing_time: float
    success_rate: float
    file_type_distribution: Dict[str, int]
    error_distribution: Dict[str, int]
    processing_trends: List[Dict[str, Any]]


class PerformanceAnalyzer:
    """Advanced performance analyzer for document processing."""
    
    def __init__(self, data_dir: str = "analytics_data"):
        """Initialize the performance analyzer."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.data_dir / "performance_metrics.json"
        self.stats_file = self.data_dir / "processing_stats.json"
        
        # Load existing data
        self.metrics = self._load_metrics()
        self.processing_history = self._load_processing_history()
    
    def _load_metrics(self) -> List[Dict[str, Any]]:
        """Load existing performance metrics."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load metrics: {e}")
        return []
    
    def _load_processing_history(self) -> List[Dict[str, Any]]:
        """Load processing history."""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load processing history: {e}")
        return []
    
    def _save_metrics(self):
        """Save metrics to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save metrics: {e}")
    
    def _save_processing_history(self):
        """Save processing history to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.processing_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save processing history: {e}")
    
    def record_processing_result(
        self,
        file_path: str,
        file_type: str,
        processing_time: float,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a processing result."""
        timestamp = datetime.now()
        
        # Record metric
        metric = {
            'timestamp': timestamp.isoformat(),
            'file_path': file_path,
            'file_type': file_type,
            'processing_time': processing_time,
            'success': success,
            'error': error,
            'metadata': metadata or {}
        }
        
        self.metrics.append(metric)
        self._save_metrics()
        
        # Update processing history
        self._update_processing_history(metric)
    
    def _update_processing_history(self, metric: Dict[str, Any]):
        """Update processing history with new metric."""
        # Group by date for trend analysis
        date_key = metric['timestamp'][:10]  # YYYY-MM-DD
        
        # Find existing entry for this date
        existing_entry = None
        for entry in self.processing_history:
            if entry.get('date') == date_key:
                existing_entry = entry
                break
        
        if existing_entry:
            # Update existing entry
            existing_entry['total_documents'] += 1
            existing_entry['total_processing_time'] += metric['processing_time']
            existing_entry['processing_times'].append(metric['processing_time'])
            
            if metric['success']:
                existing_entry['successful_documents'] += 1
            else:
                existing_entry['failed_documents'] += 1
                existing_entry['errors'].append(metric['error'])
            
            # Update file type distribution
            file_type = metric['file_type']
            existing_entry['file_type_distribution'][file_type] = \
                existing_entry['file_type_distribution'].get(file_type, 0) + 1
        else:
            # Create new entry
            new_entry = {
                'date': date_key,
                'total_documents': 1,
                'successful_documents': 1 if metric['success'] else 0,
                'failed_documents': 0 if metric['success'] else 1,
                'total_processing_time': metric['processing_time'],
                'processing_times': [metric['processing_time']],
                'errors': [] if metric['success'] else [metric['error']],
                'file_type_distribution': {metric['file_type']: 1}
            }
            self.processing_history.append(new_entry)
        
        self._save_processing_history()
    
    def get_performance_summary(self, days: int = 30) -> ProcessingStats:
        """Get performance summary for the specified number of days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Filter metrics by date
        recent_metrics = [
            m for m in self.metrics
            if m['timestamp'] >= cutoff_str
        ]
        
        if not recent_metrics:
            return ProcessingStats(
                total_documents=0,
                successful_documents=0,
                failed_documents=0,
                average_processing_time=0.0,
                total_processing_time=0.0,
                fastest_processing_time=0.0,
                slowest_processing_time=0.0,
                success_rate=0.0,
                file_type_distribution={},
                error_distribution={},
                processing_trends=[]
            )
        
        # Calculate statistics
        processing_times = [m['processing_time'] for m in recent_metrics]
        successful = [m for m in recent_metrics if m['success']]
        failed = [m for m in recent_metrics if not m['success']]
        
        # File type distribution
        file_type_dist = Counter(m['file_type'] for m in recent_metrics)
        
        # Error distribution
        error_dist = Counter(m['error'] for m in failed if m['error'])
        
        # Processing trends
        trends = self._calculate_processing_trends(recent_metrics)
        
        return ProcessingStats(
            total_documents=len(recent_metrics),
            successful_documents=len(successful),
            failed_documents=len(failed),
            average_processing_time=statistics.mean(processing_times),
            total_processing_time=sum(processing_times),
            fastest_processing_time=min(processing_times),
            slowest_processing_time=max(processing_times),
            success_rate=len(successful) / len(recent_metrics),
            file_type_distribution=dict(file_type_dist),
            error_distribution=dict(error_dist),
            processing_trends=trends
        )
    
    def _calculate_processing_trends(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate processing trends over time."""
        # Group by hour for trend analysis
        hourly_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'success_count': 0,
            'error_count': 0
        })
        
        for metric in metrics:
            # Extract hour from timestamp
            timestamp = datetime.fromisoformat(metric['timestamp'])
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            
            hourly_stats[hour_key]['count'] += 1
            hourly_stats[hour_key]['total_time'] += metric['processing_time']
            
            if metric['success']:
                hourly_stats[hour_key]['success_count'] += 1
            else:
                hourly_stats[hour_key]['error_count'] += 1
        
        # Convert to list and calculate averages
        trends = []
        for hour, stats in sorted(hourly_stats.items()):
            trends.append({
                'hour': hour,
                'document_count': stats['count'],
                'average_processing_time': stats['total_time'] / stats['count'],
                'success_rate': stats['success_count'] / stats['count'],
                'error_rate': stats['error_count'] / stats['count']
            })
        
        return trends
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance data."""
        recommendations = []
        
        # Get recent performance data
        stats = self.get_performance_summary(days=7)
        
        # Check success rate
        if stats.success_rate < 0.9:
            recommendations.append({
                'type': 'success_rate',
                'priority': 'high',
                'issue': f'Low success rate: {stats.success_rate:.1%}',
                'recommendation': 'Review error patterns and improve error handling',
                'impact': 'high'
            })
        
        # Check processing time
        if stats.average_processing_time > 5.0:  # More than 5 seconds
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'issue': f'Slow processing: {stats.average_processing_time:.2f}s average',
                'recommendation': 'Optimize parsing algorithms and consider caching',
                'impact': 'medium'
            })
        
        # Check file type distribution
        if len(stats.file_type_distribution) > 5:
            recommendations.append({
                'type': 'file_types',
                'priority': 'low',
                'issue': f'Many file types: {len(stats.file_type_distribution)} types',
                'recommendation': 'Consider standardizing on fewer file formats',
                'impact': 'low'
            })
        
        # Check error patterns
        if stats.error_distribution:
            most_common_error = max(stats.error_distribution.items(), key=lambda x: x[1])
            recommendations.append({
                'type': 'error_pattern',
                'priority': 'high',
                'issue': f'Common error: {most_common_error[0]} ({most_common_error[1]} occurrences)',
                'recommendation': 'Investigate and fix this specific error pattern',
                'impact': 'high'
            })
        
        return recommendations
    
    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        # Get different time period summaries
        daily_stats = self.get_performance_summary(days=1)
        weekly_stats = self.get_performance_summary(days=7)
        monthly_stats = self.get_performance_summary(days=30)
        
        # Get recommendations
        recommendations = self.get_optimization_recommendations()
        
        # Calculate key performance indicators
        kpis = {
            'daily_success_rate': daily_stats.success_rate,
            'weekly_success_rate': weekly_stats.success_rate,
            'monthly_success_rate': monthly_stats.success_rate,
            'daily_avg_processing_time': daily_stats.average_processing_time,
            'weekly_avg_processing_time': weekly_stats.average_processing_time,
            'monthly_avg_processing_time': monthly_stats.average_processing_time,
            'total_documents_processed': monthly_stats.total_documents,
            'total_processing_time': monthly_stats.total_processing_time
        }
        
        return {
            'kpis': kpis,
            'daily_stats': {
                'total_documents': daily_stats.total_documents,
                'successful_documents': daily_stats.successful_documents,
                'failed_documents': daily_stats.failed_documents,
                'success_rate': daily_stats.success_rate,
                'average_processing_time': daily_stats.average_processing_time,
                'file_type_distribution': daily_stats.file_type_distribution
            },
            'weekly_stats': {
                'total_documents': weekly_stats.total_documents,
                'successful_documents': weekly_stats.successful_documents,
                'failed_documents': weekly_stats.failed_documents,
                'success_rate': weekly_stats.success_rate,
                'average_processing_time': weekly_stats.average_processing_time,
                'file_type_distribution': weekly_stats.file_type_distribution
            },
            'monthly_stats': {
                'total_documents': monthly_stats.total_documents,
                'successful_documents': monthly_stats.successful_documents,
                'failed_documents': monthly_stats.failed_documents,
                'success_rate': monthly_stats.success_rate,
                'average_processing_time': monthly_stats.average_processing_time,
                'file_type_distribution': monthly_stats.file_type_distribution
            },
            'trends': monthly_stats.processing_trends,
            'error_distribution': monthly_stats.error_distribution,
            'recommendations': recommendations,
            'last_updated': datetime.now().isoformat()
        }
    
    def export_analytics_report(self, output_file: str = None) -> str:
        """Export a comprehensive analytics report."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.data_dir / f"analytics_report_{timestamp}.json"
        
        dashboard_data = self.get_performance_dashboard_data()
        
        # Add additional analysis
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_period': '30 days',
                'total_metrics_analyzed': len(self.metrics)
            },
            'dashboard_data': dashboard_data,
            'detailed_metrics': self.metrics[-100:],  # Last 100 metrics
            'processing_history': self.processing_history
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Analytics report exported to {output_file}")
        return str(output_file)


class RealTimeMonitor:
    """Real-time performance monitoring."""
    
    def __init__(self, analyzer: PerformanceAnalyzer):
        """Initialize the real-time monitor."""
        self.analyzer = analyzer
        self.active_processes = {}
        self.alerts = []
    
    def start_monitoring_process(self, process_id: str, file_path: str):
        """Start monitoring a process."""
        self.active_processes[process_id] = {
            'file_path': file_path,
            'start_time': time.time(),
            'status': 'running'
        }
    
    def update_process_progress(self, process_id: str, progress: float, step: str):
        """Update process progress."""
        if process_id in self.active_processes:
            self.active_processes[process_id].update({
                'progress': progress,
                'current_step': step,
                'last_update': time.time()
            })
    
    def complete_process(self, process_id: str, success: bool, error: str = None):
        """Mark a process as completed."""
        if process_id in self.active_processes:
            process = self.active_processes[process_id]
            process['status'] = 'completed' if success else 'failed'
            process['end_time'] = time.time()
            process['duration'] = process['end_time'] - process['start_time']
            process['success'] = success
            process['error'] = error
            
            # Record in analyzer
            self.analyzer.record_processing_result(
                file_path=process['file_path'],
                file_type=Path(process['file_path']).suffix,
                processing_time=process['duration'],
                success=success,
                error=error
            )
    
    def get_active_processes(self) -> Dict[str, Any]:
        """Get currently active processes."""
        return self.active_processes.copy()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        # Get recent performance
        recent_stats = self.analyzer.get_performance_summary(days=1)
        
        # Calculate health score
        health_score = 100.0
        
        # Deduct points for issues
        if recent_stats.success_rate < 0.95:
            health_score -= 20
        if recent_stats.average_processing_time > 10.0:
            health_score -= 15
        if recent_stats.failed_documents > 5:
            health_score -= 10
        
        # Determine health status
        if health_score >= 90:
            status = 'excellent'
        elif health_score >= 75:
            status = 'good'
        elif health_score >= 60:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'health_score': health_score,
            'status': status,
            'active_processes': len(self.active_processes),
            'recent_success_rate': recent_stats.success_rate,
            'recent_avg_processing_time': recent_stats.average_processing_time,
            'recommendations': self.analyzer.get_optimization_recommendations()
        } 