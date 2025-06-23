#!/usr/bin/env python3
"""
Provenance Tracking Module
Maintains detailed audit trails of all data sources, transformations, and decisions made during documentation generation.
"""

import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """Represents a source of data used in documentation generation."""
    id: str
    name: str
    type: str  # 'pdf', 'docx', 'xml', 'json', 'manual_input'
    path: str
    hash: str
    size_bytes: int
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class TransformationStep:
    """Represents a transformation step in the documentation generation process."""
    id: str
    step_name: str
    step_type: str  # 'parsing', 'matching', 'generation', 'enhancement', 'validation'
    input_sources: List[str]
    output_artifacts: List[str]
    parameters: Dict[str, Any]
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class DecisionPoint:
    """Represents a decision made during the documentation generation process."""
    id: str
    decision_type: str  # 'template_matching', 'content_selection', 'gap_identification', 'confidence_assessment'
    context: str
    options: List[str]
    selected_option: str
    reasoning: str
    confidence: float
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ProvenanceRecord:
    """Complete provenance record for a documentation generation session."""
    session_id: str
    document_title: str
    data_sources: List[DataSource]
    transformations: List[TransformationStep]
    decisions: List[DecisionPoint]
    final_artifacts: List[str]
    generation_time: float
    created_at: str
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProvenanceTracker:
    """Tracks provenance information throughout the documentation generation process."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.data_sources: List[DataSource] = []
        self.transformations: List[TransformationStep] = []
        self.decisions: List[DecisionPoint] = []
        self.final_artifacts: List[str] = []
        self.start_time = time.time()
        self.document_title = ""
        
        logger.info(f"Initialized provenance tracker for session: {self.session_id}")
    
    def add_data_source(self, name: str, file_path: str, source_type: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a data source to the provenance record."""
        try:
            path = Path(file_path)
            if path.exists():
                file_hash = self._calculate_file_hash(file_path)
                size_bytes = path.stat().st_size
            else:
                file_hash = "unknown"
                size_bytes = 0
            
            source_id = f"source_{len(self.data_sources) + 1}"
            
            data_source = DataSource(
                id=source_id,
                name=name,
                type=source_type,
                path=str(file_path),
                hash=file_hash,
                size_bytes=size_bytes,
                timestamp=datetime.now().isoformat(),
                metadata=metadata or {}
            )
            
            self.data_sources.append(data_source)
            logger.info(f"Added data source: {name} ({source_type})")
            
            return source_id
            
        except Exception as e:
            logger.error(f"Failed to add data source {name}: {e}")
            return f"error_source_{len(self.data_sources) + 1}"
    
    def add_transformation(self, step_name: str, step_type: str, 
                          input_sources: List[str], output_artifacts: List[str],
                          parameters: Dict[str, Any], execution_time: float,
                          success: bool, error_message: Optional[str] = None) -> str:
        """Add a transformation step to the provenance record."""
        transformation_id = f"transform_{len(self.transformations) + 1}"
        
        transformation = TransformationStep(
            id=transformation_id,
            step_name=step_name,
            step_type=step_type,
            input_sources=input_sources,
            output_artifacts=output_artifacts,
            parameters=parameters,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )
        
        self.transformations.append(transformation)
        logger.info(f"Added transformation: {step_name} ({step_type}) - {'SUCCESS' if success else 'FAILED'}")
        
        return transformation_id
    
    def add_decision(self, decision_type: str, context: str, options: List[str],
                    selected_option: str, reasoning: str, confidence: float) -> str:
        """Add a decision point to the provenance record."""
        decision_id = f"decision_{len(self.decisions) + 1}"
        
        decision = DecisionPoint(
            id=decision_id,
            decision_type=decision_type,
            context=context,
            options=options,
            selected_option=selected_option,
            reasoning=reasoning,
            confidence=confidence
        )
        
        self.decisions.append(decision)
        logger.info(f"Added decision: {decision_type} - {selected_option} (confidence: {confidence:.2f})")
        
        return decision_id
    
    def add_final_artifact(self, artifact_path: str):
        """Add a final artifact to the provenance record."""
        self.final_artifacts.append(artifact_path)
        logger.info(f"Added final artifact: {artifact_path}")
    
    def set_document_title(self, title: str):
        """Set the document title for the provenance record."""
        self.document_title = title
        logger.info(f"Set document title: {title}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return "hash_calculation_failed"
    
    def get_provenance_record(self) -> ProvenanceRecord:
        """Get the complete provenance record."""
        generation_time = time.time() - self.start_time
        
        return ProvenanceRecord(
            session_id=self.session_id,
            document_title=self.document_title,
            data_sources=self.data_sources,
            transformations=self.transformations,
            decisions=self.decisions,
            final_artifacts=self.final_artifacts,
            generation_time=generation_time,
            created_at=datetime.now().isoformat(),
            metadata={
                "total_sources": len(self.data_sources),
                "total_transformations": len(self.transformations),
                "total_decisions": len(self.decisions),
                "successful_transformations": len([t for t in self.transformations if t.success]),
                "failed_transformations": len([t for t in self.transformations if not t.success])
            }
        )
    
    def save_provenance(self, output_path: str):
        """Save provenance record to file."""
        try:
            record = self.get_provenance_record()
            output_data = asdict(record)
            
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"Provenance record saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save provenance record: {e}")
    
    def export_provenance_summary(self, output_path: str):
        """Export a human-readable provenance summary."""
        try:
            record = self.get_provenance_record()
            
            summary_lines = []
            summary_lines.append(f"# Provenance Summary: {record.document_title}")
            summary_lines.append("")
            summary_lines.append(f"**Session ID:** {record.session_id}")
            summary_lines.append(f"**Generated:** {record.created_at}")
            summary_lines.append(f"**Total Time:** {record.generation_time:.2f} seconds")
            summary_lines.append("")
            
            # Data Sources
            summary_lines.append("## Data Sources")
            summary_lines.append("")
            for source in record.data_sources:
                summary_lines.append(f"### {source.name}")
                summary_lines.append(f"- **Type:** {source.type}")
                summary_lines.append(f"- **Path:** {source.path}")
                summary_lines.append(f"- **Size:** {source.size_bytes} bytes")
                summary_lines.append(f"- **Hash:** {source.hash[:16]}...")
                summary_lines.append(f"- **Added:** {source.timestamp}")
                summary_lines.append("")
            
            # Transformations
            summary_lines.append("## Transformations")
            summary_lines.append("")
            for transform in record.transformations:
                status = "✅ SUCCESS" if transform.success else "❌ FAILED"
                summary_lines.append(f"### {transform.step_name} {status}")
                summary_lines.append(f"- **Type:** {transform.step_type}")
                summary_lines.append(f"- **Input Sources:** {', '.join(transform.input_sources)}")
                summary_lines.append(f"- **Output Artifacts:** {', '.join(transform.output_artifacts)}")
                summary_lines.append(f"- **Execution Time:** {transform.execution_time:.2f}s")
                summary_lines.append(f"- **Timestamp:** {transform.timestamp}")
                if transform.error_message:
                    summary_lines.append(f"- **Error:** {transform.error_message}")
                summary_lines.append("")
            
            # Decisions
            summary_lines.append("## Key Decisions")
            summary_lines.append("")
            for decision in record.decisions:
                summary_lines.append(f"### {decision.decision_type}")
                summary_lines.append(f"- **Context:** {decision.context}")
                summary_lines.append(f"- **Options:** {', '.join(decision.options)}")
                summary_lines.append(f"- **Selected:** {decision.selected_option}")
                summary_lines.append(f"- **Reasoning:** {decision.reasoning}")
                summary_lines.append(f"- **Confidence:** {decision.confidence:.2f}")
                summary_lines.append(f"- **Timestamp:** {decision.timestamp}")
                summary_lines.append("")
            
            # Final Artifacts
            summary_lines.append("## Final Artifacts")
            summary_lines.append("")
            for artifact in record.final_artifacts:
                summary_lines.append(f"- {artifact}")
            summary_lines.append("")
            
            # Statistics
            summary_lines.append("## Statistics")
            summary_lines.append("")
            summary_lines.append(f"- **Total Data Sources:** {len(record.data_sources)}")
            summary_lines.append(f"- **Total Transformations:** {len(record.transformations)}")
            summary_lines.append(f"- **Successful Transformations:** {len([t for t in record.transformations if t.success])}")
            summary_lines.append(f"- **Failed Transformations:** {len([t for t in record.transformations if not t.success])}")
            summary_lines.append(f"- **Total Decisions:** {len(record.decisions)}")
            summary_lines.append(f"- **Final Artifacts:** {len(record.final_artifacts)}")
            
            with open(output_path, 'w') as f:
                f.write('\n'.join(summary_lines))
            
            logger.info(f"Provenance summary exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export provenance summary: {e}")
    
    def get_data_lineage(self, artifact_id: str) -> Dict[str, Any]:
        """Get the lineage of a specific artifact."""
        lineage = {
            "artifact_id": artifact_id,
            "sources": [],
            "transformations": [],
            "decisions": []
        }
        
        # Find transformations that produced this artifact
        for transform in self.transformations:
            if artifact_id in transform.output_artifacts:
                lineage["transformations"].append(transform)
                
                # Add input sources
                for source_id in transform.input_sources:
                    source = next((s for s in self.data_sources if s.id == source_id), None)
                    if source and source not in lineage["sources"]:
                        lineage["sources"].append(source)
        
        # Find decisions related to this artifact
        for decision in self.decisions:
            if artifact_id in decision.context:
                lineage["decisions"].append(decision)
        
        return lineage
    
    def validate_provenance_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the provenance record."""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check for orphaned transformations
        for transform in self.transformations:
            for source_id in transform.input_sources:
                if not any(s.id == source_id for s in self.data_sources):
                    validation_results["issues"].append(f"Transformation {transform.id} references unknown source {source_id}")
                    validation_results["valid"] = False
        
        # Check for failed transformations
        failed_transforms = [t for t in self.transformations if not t.success]
        if failed_transforms:
            validation_results["warnings"].append(f"Found {len(failed_transforms)} failed transformations")
        
        # Check for missing timestamps
        for source in self.data_sources:
            if not source.timestamp:
                validation_results["issues"].append(f"Data source {source.id} missing timestamp")
                validation_results["valid"] = False
        
        # Check for reasonable execution times
        for transform in self.transformations:
            if transform.execution_time < 0:
                validation_results["issues"].append(f"Transformation {transform.id} has negative execution time")
                validation_results["valid"] = False
            elif transform.execution_time > 3600:  # More than 1 hour
                validation_results["warnings"].append(f"Transformation {transform.id} took {transform.execution_time:.2f}s")
        
        return validation_results


def main():
    """Test the provenance tracker."""
    # Initialize tracker
    tracker = ProvenanceTracker()
    tracker.set_document_title("Cisco Nexus 9000 Installation Guide")
    
    # Add data sources
    source1_id = tracker.add_data_source(
        name="Nexus Hardware Guide",
        file_path="nexus_guide.pdf",
        source_type="pdf",
        metadata={"pages": 150, "version": "1.0"}
    )
    
    source2_id = tracker.add_data_source(
        name="Installation Requirements",
        file_path="requirements.json",
        source_type="json",
        metadata={"format": "structured"}
    )
    
    # Add transformations
    transform1_id = tracker.add_transformation(
        step_name="PDF Text Extraction",
        step_type="parsing",
        input_sources=[source1_id],
        output_artifacts=["extracted_text.txt"],
        parameters={"method": "pdfplumber", "pages": "all"},
        execution_time=2.5,
        success=True
    )
    
    transform2_id = tracker.add_transformation(
        step_name="Template Matching",
        step_type="matching",
        input_sources=[source1_id, source2_id],
        output_artifacts=["matched_sections.json"],
        parameters={"algorithm": "jaccard_similarity", "threshold": 0.3},
        execution_time=1.8,
        success=True
    )
    
    # Add decisions
    decision1_id = tracker.add_decision(
        decision_type="template_matching",
        context="Hardware Overview section",
        options=["hardware_overview", "installation_prep", "configuration"],
        selected_option="hardware_overview",
        reasoning="High keyword overlap with hardware specifications",
        confidence=0.85
    )
    
    # Add final artifacts
    tracker.add_final_artifact("draft_nexus_guide.md")
    tracker.add_final_artifact("gap_analysis.json")
    
    # Save provenance
    tracker.save_provenance("test_provenance.json")
    tracker.export_provenance_summary("test_provenance_summary.md")
    
    # Validate integrity
    validation = tracker.validate_provenance_integrity()
    
    print(f"✅ Provenance tracking completed!")
    print(f"   Session ID: {tracker.session_id}")
    print(f"   Data sources: {len(tracker.data_sources)}")
    print(f"   Transformations: {len(tracker.transformations)}")
    print(f"   Decisions: {len(tracker.decisions)}")
    print(f"   Integrity valid: {validation['valid']}")


if __name__ == "__main__":
    main()
