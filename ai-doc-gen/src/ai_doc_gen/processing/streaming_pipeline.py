"""
Real-time Streaming Document Processing Pipeline

This module provides real-time document processing capabilities with async support,
progress tracking, and streaming results.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStep:
    """Represents a processing step in the pipeline."""
    name: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    progress: float = 0.0  # 0.0 to 1.0
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    success: bool
    steps: List[ProcessingStep]
    total_duration: float
    final_result: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamingDocumentPipeline:
    """Real-time streaming document processing pipeline."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize the streaming pipeline."""
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.progress_callbacks: List[Callable] = []
        self.step_callbacks: List[Callable] = []
        
    def add_progress_callback(self, callback: Callable[[str, float], None]):
        """Add a progress callback function."""
        self.progress_callbacks.append(callback)
    
    def add_step_callback(self, callback: Callable[[ProcessingStep], None]):
        """Add a step completion callback function."""
        self.step_callbacks.append(callback)
    
    async def process_document_streaming(
        self, 
        file_path: str,
        steps: List[Dict[str, Any]]
    ) -> AsyncGenerator[ProcessingStep, None]:
        """Process a document with streaming results."""
        
        # Initialize pipeline
        pipeline_steps = []
        for step_config in steps:
            step = ProcessingStep(
                name=step_config['name'],
                metadata=step_config.get('metadata', {})
            )
            pipeline_steps.append(step)
        
        # Process each step
        for i, step in enumerate(pipeline_steps):
            try:
                # Update step status
                step.status = "running"
                step.start_time = time.time()
                
                # Yield step start
                yield step
                
                # Execute step
                if step_config['type'] == 'async':
                    result = await self._execute_async_step(step_config, file_path, step)
                else:
                    result = await self._execute_sync_step(step_config, file_path, step)
                
                # Update step completion
                step.status = "completed"
                step.end_time = time.time()
                step.duration = step.end_time - step.start_time
                step.progress = 1.0
                step.result = result
                
                # Yield completed step
                yield step
                
                # Notify callbacks
                for callback in self.step_callbacks:
                    callback(step)
                
            except Exception as e:
                # Handle step failure
                step.status = "failed"
                step.end_time = time.time()
                step.duration = step.end_time - step.start_time
                step.error = str(e)
                
                logger.error(f"Step '{step.name}' failed: {e}")
                
                # Yield failed step
                yield step
                
                # Notify callbacks
                for callback in self.step_callbacks:
                    callback(step)
                
                break
    
    async def _execute_async_step(
        self, 
        step_config: Dict[str, Any], 
        file_path: str, 
        step: ProcessingStep
    ) -> Any:
        """Execute an async processing step."""
        step_func = step_config['function']
        
        # Execute with progress updates
        if 'progress_updates' in step_config:
            for progress in step_config['progress_updates']:
                step.progress = progress
                await asyncio.sleep(0.1)  # Allow other tasks to run
        
        # Execute the actual function
        if asyncio.iscoroutinefunction(step_func):
            result = await step_func(file_path, step)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, step_func, file_path, step)
        
        return result
    
    async def _execute_sync_step(
        self, 
        step_config: Dict[str, Any], 
        file_path: str, 
        step: ProcessingStep
    ) -> Any:
        """Execute a sync processing step."""
        step_func = step_config['function']
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, step_func, file_path, step)
        
        return result
    
    async def process_multiple_documents(
        self, 
        file_paths: List[str],
        steps: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[PipelineResult]:
        """Process multiple documents concurrently."""
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_document(file_path: str) -> PipelineResult:
            async with semaphore:
                return await self.process_document(file_path, steps)
        
        # Process all documents concurrently
        tasks = [process_single_document(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        pipeline_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Document {file_paths[i]} failed: {result}")
                pipeline_results.append(PipelineResult(
                    success=False,
                    steps=[],
                    total_duration=0.0,
                    errors=[str(result)]
                ))
            else:
                pipeline_results.append(result)
        
        return pipeline_results
    
    async def process_document(
        self, 
        file_path: str, 
        steps: List[Dict[str, Any]]
    ) -> PipelineResult:
        """Process a single document and return complete result."""
        
        pipeline_steps = []
        errors = []
        start_time = time.time()
        
        try:
            # Process each step
            async for step in self.process_document_streaming(file_path, steps):
                pipeline_steps.append(step)
                
                if step.status == "failed":
                    errors.append(f"Step '{step.name}': {step.error}")
            
            # Calculate total duration
            total_duration = time.time() - start_time
            
            # Determine success
            success = len(errors) == 0
            
            # Get final result from last successful step
            final_result = None
            for step in reversed(pipeline_steps):
                if step.status == "completed" and step.result is not None:
                    final_result = step.result
                    break
            
            return PipelineResult(
                success=success,
                steps=pipeline_steps,
                total_duration=total_duration,
                final_result=final_result,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Pipeline failed for {file_path}: {e}")
            return PipelineResult(
                success=False,
                steps=pipeline_steps,
                total_duration=time.time() - start_time,
                errors=[str(e)]
            )


class DocumentProcessor:
    """High-level document processor with streaming capabilities."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.pipeline = StreamingDocumentPipeline()
        
        # Define standard processing steps
        self.standard_steps = [
            {
                'name': 'validation',
                'type': 'sync',
                'function': self._validate_document,
                'metadata': {'description': 'Validate document format and content'}
            },
            {
                'name': 'parsing',
                'type': 'async',
                'function': self._parse_document,
                'metadata': {'description': 'Parse document structure'},
                'progress_updates': [0.25, 0.5, 0.75, 1.0]
            },
            {
                'name': 'entity_extraction',
                'type': 'async',
                'function': self._extract_entities,
                'metadata': {'description': 'Extract technical entities'},
                'progress_updates': [0.33, 0.66, 1.0]
            },
            {
                'name': 'classification',
                'type': 'async',
                'function': self._classify_sections,
                'metadata': {'description': 'Classify document sections'},
                'progress_updates': [0.5, 1.0]
            },
            {
                'name': 'template_matching',
                'type': 'async',
                'function': self._match_template,
                'metadata': {'description': 'Match sections to template'},
                'progress_updates': [0.25, 0.5, 0.75, 1.0]
            }
        ]
    
    async def _validate_document(self, file_path: str, step: ProcessingStep) -> Dict[str, Any]:
        """Validate document format and content."""
        from ..input_processing.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_document(file_path)
        
        return {
            'is_valid': result.is_valid,
            'score': result.score,
            'issues': [issue.message for issue in result.issues],
            'warnings': [warning.message for warning in result.warnings]
        }
    
    async def _parse_document(self, file_path: str, step: ProcessingStep) -> Dict[str, Any]:
        """Parse document structure."""
        from ..input_processing.document_parser import DocumentParserFactory
        
        factory = DocumentParserFactory()
        parser = factory.get_parser(file_path)
        
        if not parser:
            raise ValueError(f"No parser found for {file_path}")
        
        parsed_doc = parser.parse(file_path)
        
        return {
            'sections': parsed_doc.sections,
            'title': parsed_doc.title,
            'metadata': parsed_doc.metadata,
            'section_count': len(parsed_doc.sections)
        }
    
    async def _extract_entities(self, file_path: str, step: ProcessingStep) -> Dict[str, Any]:
        """Extract technical entities."""
        from ..nlp.entity_extractor import DocumentEntityAnalyzer
        
        # Get parsed document from previous step
        parsed_result = step.result if hasattr(step, 'result') else None
        if not parsed_result:
            raise ValueError("No parsed document available for entity extraction")
        
        analyzer = DocumentEntityAnalyzer()
        entity_analysis = analyzer.analyze_document(parsed_result['sections'])
        
        return entity_analysis
    
    async def _classify_sections(self, file_path: str, step: ProcessingStep) -> Dict[str, Any]:
        """Classify document sections."""
        from ..ml.section_classifier import SectionClassifier
        
        # Get parsed document from previous step
        parsed_result = step.result if hasattr(step, 'result') else None
        if not parsed_result:
            raise ValueError("No parsed document available for classification")
        
        classifier = SectionClassifier()
        classified_sections = classifier.classify_sections(parsed_result['sections'])
        insights = classifier.get_classification_insights(parsed_result['sections'])
        
        return {
            'classified_sections': classified_sections,
            'insights': insights
        }
    
    async def _match_template(self, file_path: str, step: ProcessingStep) -> Dict[str, Any]:
        """Match sections to template."""
        # This would integrate with the existing template matching system
        # For now, return a placeholder result
        return {
            'template_matches': [],
            'coverage': 0.0,
            'confidence': 0.0
        }
    
    async def process_document_streaming(
        self, 
        file_path: str,
        custom_steps: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[ProcessingStep, None]:
        """Process a document with streaming results."""
        steps = custom_steps or self.standard_steps
        
        async for step in self.pipeline.process_document_streaming(file_path, steps):
            yield step
    
    async def process_document_complete(
        self, 
        file_path: str,
        custom_steps: Optional[List[Dict[str, Any]]] = None
    ) -> PipelineResult:
        """Process a document and return complete result."""
        steps = custom_steps or self.standard_steps
        
        return await self.pipeline.process_document(file_path, steps)
    
    async def process_multiple_documents(
        self, 
        file_paths: List[str],
        custom_steps: Optional[List[Dict[str, Any]]] = None,
        max_concurrent: int = 3
    ) -> List[PipelineResult]:
        """Process multiple documents concurrently."""
        steps = custom_steps or self.standard_steps
        
        return await self.pipeline.process_multiple_documents(
            file_paths, steps, max_concurrent
        )


class ProgressTracker:
    """Track and report processing progress."""
    
    def __init__(self):
        """Initialize the progress tracker."""
        self.total_documents = 0
        self.completed_documents = 0
        self.failed_documents = 0
        self.current_document = None
        self.current_step = None
        self.start_time = None
        self.estimated_completion = None
    
    def start_processing(self, total_documents: int):
        """Start tracking processing."""
        self.total_documents = total_documents
        self.completed_documents = 0
        self.failed_documents = 0
        self.start_time = time.time()
    
    def update_progress(self, document: str, step: str, progress: float):
        """Update progress for current document and step."""
        self.current_document = document
        self.current_step = step
        
        # Estimate completion time
        if self.completed_documents > 0:
            avg_time_per_doc = (time.time() - self.start_time) / self.completed_documents
            remaining_docs = self.total_documents - self.completed_documents
            self.estimated_completion = time.time() + (avg_time_per_doc * remaining_docs)
    
    def document_completed(self, success: bool = True):
        """Mark a document as completed."""
        self.completed_documents += 1
        if not success:
            self.failed_documents += 1
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        if self.total_documents == 0:
            return {'status': 'not_started'}
        
        progress_percentage = (self.completed_documents / self.total_documents) * 100
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'total_documents': self.total_documents,
            'completed_documents': self.completed_documents,
            'failed_documents': self.failed_documents,
            'progress_percentage': progress_percentage,
            'elapsed_time': elapsed_time,
            'estimated_completion': self.estimated_completion,
            'current_document': self.current_document,
            'current_step': self.current_step,
            'success_rate': (self.completed_documents - self.failed_documents) / self.completed_documents if self.completed_documents > 0 else 0
        } 