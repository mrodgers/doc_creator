#!/usr/bin/env python3
"""
Workflow Orchestrator
Coordinates draft generation, gap analysis, and provenance tracking for end-to-end documentation automation.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List

from .draft_generator import DraftGenerator, ContentSection
from .gap_analyzer import GapAnalyzer
from .provenance_tracker import ProvenanceTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workflow_orchestrator")


class WorkflowOrchestrator:
    """Coordinates the end-to-end documentation generation workflow."""
    def __init__(self):
        self.draft_generator = DraftGenerator()
        self.gap_analyzer = GapAnalyzer()
        self.provenance_tracker = ProvenanceTracker()

    def run(self, content_sections: List[ContentSection], document_title: str, output_dir: str = "outputs"):
        start_time = time.time()
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Starting workflow for: {document_title}")

        # Provenance: Add data sources
        for section in content_sections:
            self.provenance_tracker.add_data_source(
                name=section.title,
                file_path=section.source,
                source_type="pdf" if section.source.endswith(".pdf") else "manual_input",
                metadata={"section_id": section.id, "confidence": section.confidence}
            )
        self.provenance_tracker.set_document_title(document_title)

        # Step 1: Draft Generation
        draft_start = time.time()
        draft_result = self.draft_generator.generate_draft(content_sections, document_title)
        draft_time = time.time() - draft_start
        draft_json = f"{output_dir}/draft_result.json"
        draft_md = f"{output_dir}/draft.md"
        self.draft_generator.save_draft(draft_result, draft_json)
        self.draft_generator.export_markdown(draft_result, draft_md)
        self.provenance_tracker.add_transformation(
            step_name="Draft Generation",
            step_type="generation",
            input_sources=[s.id for s in content_sections],
            output_artifacts=[draft_json, draft_md],
            parameters={},
            execution_time=draft_time,
            success=True
        )
        self.provenance_tracker.add_final_artifact(draft_md)

        # Step 2: Gap Analysis
        gap_start = time.time()
        existing_section_ids = [s.template_match or self.draft_generator._find_best_template_match(s) for s in content_sections]
        gap_report = self.gap_analyzer.analyze_gaps(existing_section_ids, document_title)
        gap_time = time.time() - gap_start
        gap_json = f"{output_dir}/gap_report.json"
        gap_md = f"{output_dir}/gap_report.md"
        self.gap_analyzer.save_gap_report(gap_report, gap_json)
        self.gap_analyzer.export_gap_report_markdown(gap_report, gap_md)
        self.provenance_tracker.add_transformation(
            step_name="Gap Analysis",
            step_type="analysis",
            input_sources=[draft_json],
            output_artifacts=[gap_json, gap_md],
            parameters={},
            execution_time=gap_time,
            success=True
        )
        self.provenance_tracker.add_final_artifact(gap_md)

        # Step 3: Save Provenance
        provenance_json = f"{output_dir}/provenance.json"
        provenance_md = f"{output_dir}/provenance_summary.md"
        self.provenance_tracker.save_provenance(provenance_json)
        self.provenance_tracker.export_provenance_summary(provenance_md)

        total_time = time.time() - start_time
        logger.info(f"Workflow completed in {total_time:.2f}s. Outputs in: {output_dir}")
        return {
            "draft_json": draft_json,
            "draft_md": draft_md,
            "gap_json": gap_json,
            "gap_md": gap_md,
            "provenance_json": provenance_json,
            "provenance_md": provenance_md,
            "total_time": total_time
        }


def main():
    """End-to-end test of the workflow orchestrator with sample data."""
    # Sample content sections
    content_sections = [
        ContentSection(
            id="section_1",
            title="Nexus Hardware Overview",
            content="The Cisco Nexus 9000 Series switches provide high-performance, low-latency switching for data center environments.",
            source="nexus_guide.pdf",
            confidence=0.9,
            acronyms_found=[("Nexus", "Cisco Nexus"), ("Nexus 9000", "Cisco Nexus 9000 Series")]
        ),
        ContentSection(
            id="section_2",
            title="Installation Requirements",
            content="Before installing the Nexus switch, ensure you have the required tools and safety equipment.",
            source="nexus_guide.pdf",
            confidence=0.8,
            acronyms_found=[]
        ),
        ContentSection(
            id="section_3",
            title="Initial Configuration",
            content="Configure the management interface and assign an IP address to the switch.",
            source="nexus_guide.pdf",
            confidence=0.85,
            acronyms_found=[]
        )
    ]
    orchestrator = WorkflowOrchestrator()
    outputs = orchestrator.run(content_sections, "Cisco Nexus 9000 Installation Guide")
    print("\n✅ End-to-end workflow completed!")
    for k, v in outputs.items():
        if k.endswith('_md') or k.endswith('_json'):
            print(f"  {k}: {v}")
    print(f"  Total time: {outputs['total_time']:.2f}s")


if __name__ == "__main__":
    main() 