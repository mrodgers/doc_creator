"""
Enhanced Pipeline Orchestrator

Based on the original pipeline_runner.py but enhanced for:
- Multi-agent architecture (Managing Agent, Review Agent)
- Async operations
- Better error handling and rollback
- Comprehensive metrics collection
- Modular step execution
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel

from .confidence_scoring import ConfidenceScorer
from .gap_analyzer import GapAnalyzer
from .llm_integration import LLMClient
from .provenance_tracker import ProvenanceTracker

logger = logging.getLogger(__name__)

@dataclass
class PipelineStep:
    """Individual pipeline step with metadata."""
    name: str
    function: Callable
    required_inputs: List[str]
    outputs: List[str]
    timeout: int = 300  # 5 minutes default
    retry_count: int = 3
    critical: bool = True

class PipelineMetrics(BaseModel):
    """Comprehensive pipeline metrics."""
    pipeline_run: Dict[str, Any]
    extraction_metrics: Dict[str, Any]
    confidence_metrics: Dict[str, Any]
    gap_analysis_metrics: Dict[str, Any]
    provenance_metrics: Dict[str, Any]
    agent_metrics: Dict[str, Any]
    file_outputs: Dict[str, str]

class PipelineOrchestrator:
    """Enhanced pipeline orchestrator for multi-agent documentation generation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pipeline orchestrator with configuration."""
        self.config = config or {}
        self.steps: List[PipelineStep] = []
        self.metrics = PipelineMetrics(
            pipeline_run={},
            extraction_metrics={},
            confidence_metrics={},
            gap_analysis_metrics={},
            provenance_metrics={},
            agent_metrics={},
            file_outputs={}
        )

        # Initialize core components
        self.llm_client = LLMClient(
            provider=self.config.get("llm_provider", "openai")
        )
        self.confidence_scorer = ConfidenceScorer(
            default_threshold=self.config.get("confidence_threshold", 85.0)
        )
        self.gap_analyzer = GapAnalyzer(
            confidence_threshold=self.config.get("gap_threshold", 70.0)
        )
        self.provenance_tracker = ProvenanceTracker()

        # Pipeline state
        self.current_step = 0
        self.pipeline_state: Dict[str, Any] = {}
        self.error_log: List[Dict[str, Any]] = []

        # Register default steps
        self._register_default_steps()

    def _register_default_steps(self) -> None:
        """Register default pipeline steps."""
        self.add_step(
            PipelineStep(
                name="input_processing",
                function=self._process_inputs,
                required_inputs=["input_files"],
                outputs=["structured_content"],
                timeout=600
            )
        )

        self.add_step(
            PipelineStep(
                name="managing_agent_analysis",
                function=self._run_managing_agent,
                required_inputs=["structured_content"],
                outputs=["initial_analysis", "confidence_scores"],
                timeout=900
            )
        )

        self.add_step(
            PipelineStep(
                name="gap_analysis",
                function=self._run_gap_analysis,
                required_inputs=["initial_analysis", "confidence_scores"],
                outputs=["gap_report", "sme_questions"],
                timeout=300
            )
        )

        self.add_step(
            PipelineStep(
                name="review_agent_validation",
                function=self._run_review_agent,
                required_inputs=["initial_analysis", "gap_report"],
                outputs=["validated_analysis", "provenance_report"],
                timeout=600
            )
        )

        self.add_step(
            PipelineStep(
                name="draft_generation",
                function=self._generate_draft,
                required_inputs=["validated_analysis", "gap_report"],
                outputs=["draft_document", "final_metrics"],
                timeout=1200
            )
        )

    def add_step(self, step: PipelineStep) -> None:
        """Add a custom pipeline step."""
        self.steps.append(step)
        logger.info(f"Added pipeline step: {step.name}")

    async def run_pipeline(
        self,
        input_files: List[str],
        output_dir: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the complete documentation generation pipeline."""

        start_time = time.time()
        logger.info("Starting AI-Assisted Documentation Generation Pipeline")

        # Initialize pipeline state
        self.pipeline_state = {
            "input_files": input_files,
            "output_dir": output_dir,
            "ground_truth": ground_truth,
            "start_time": start_time
        }

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        try:
            # Execute pipeline steps
            for i, step in enumerate(self.steps):
                self.current_step = i
                logger.info(f"Executing step {i+1}/{len(self.steps)}: {step.name}")

                # Check required inputs
                missing_inputs = self._check_required_inputs(step)
                if missing_inputs:
                    raise ValueError(f"Missing required inputs for {step.name}: {missing_inputs}")

                # Execute step with retry logic
                step_result = await self._execute_step_with_retry(step)

                # Update pipeline state with outputs
                for output_key in step.outputs:
                    if output_key in step_result:
                        self.pipeline_state[output_key] = step_result[output_key]

                logger.info(f"✅ Step {step.name} completed successfully")

            # Generate final metrics
            await self._generate_final_metrics(start_time)

            # Save pipeline results
            await self._save_pipeline_results()

            logger.info("🎉 Pipeline completed successfully!")
            return {
                "status": "success",
                "outputs": self.pipeline_state,
                "metrics": self.metrics.dict()
            }

        except Exception as e:
            logger.error(f"❌ Pipeline failed at step {self.current_step}: {e}")
            await self._handle_pipeline_failure(e)
            return {
                "status": "failed",
                "error": str(e),
                "failed_step": self.current_step,
                "error_log": self.error_log
            }

    def _check_required_inputs(self, step: PipelineStep) -> List[str]:
        """Check if required inputs are available for a step."""
        missing = []
        for input_key in step.required_inputs:
            if input_key not in self.pipeline_state:
                missing.append(input_key)
        return missing

    async def _execute_step_with_retry(self, step: PipelineStep) -> Dict[str, Any]:
        """Execute a pipeline step with retry logic."""
        last_error = None

        for attempt in range(step.retry_count):
            try:
                # Execute step with timeout
                result = await asyncio.wait_for(
                    step.function(self.pipeline_state),
                    timeout=step.timeout
                )
                return result

            except asyncio.TimeoutError:
                error_msg = f"Step {step.name} timed out after {step.timeout} seconds"
                logger.error(error_msg)
                last_error = TimeoutError(error_msg)

            except Exception as e:
                error_msg = f"Step {step.name} failed (attempt {attempt + 1}/{step.retry_count}): {e}"
                logger.error(error_msg)
                last_error = e

                if step.critical:
                    break

                # Wait before retry
                if attempt < step.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Log error and raise
        self.error_log.append({
            "step": step.name,
            "error": str(last_error),
            "timestamp": datetime.now().isoformat()
        })

        if step.critical:
            raise last_error
        else:
            logger.warning(f"Non-critical step {step.name} failed, continuing...")
            return {}

    async def _process_inputs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process input files and extract structured content using the real input processing module."""
        from ai_doc_gen.input_processing import (
            extract_structured_content,
            parse_document,
        )
        input_files = state.get("input_files", [])
        all_content = []
        for file_path in input_files:
            parsed = parse_document(file_path)
            content = extract_structured_content(parsed)
            # Convert to dicts for serialization and downstream use
            all_content.extend([c.model_dump() if hasattr(c, 'model_dump') else c.dict() for c in content])
        return {"structured_content": all_content}

    async def _run_managing_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the managing agent for initial analysis on structured content."""
        from ai_doc_gen.agents.managing_agent import ManagingAgent
        from ai_doc_gen.input_processing.structured_extractor import (
            ContentType,
            ExtractedContent,
        )
        content = state["structured_content"]
        # Rehydrate dicts to ExtractedContent objects
        hydrated_content = []
        for item in content:
            if isinstance(item, dict):
                ct = item.get("content_type")
                if isinstance(ct, ContentType):
                    content_type = ct
                elif isinstance(ct, str):
                    content_type = ContentType(ct)
                else:
                    content_type = ContentType.NOTE
                hydrated_content.append(ExtractedContent(
                    content_type=content_type,
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    confidence=item.get("confidence", 0.0),
                    source_section=item.get("source_section", ""),
                    tags=item.get("tags", [])
                ))
            else:
                hydrated_content.append(item)
        managing_agent = ManagingAgent()
        managing_results = managing_agent.run(hydrated_content)
        # Track provenance for each item
        for item in hydrated_content:
            self.provenance_tracker.add_provenance_entry(
                item_id=item.title,
                item_type=item.content_type.value if hasattr(item.content_type, 'value') else str(item.content_type),
                value=item.content,
                source_document=state["input_files"][0] if state["input_files"] else "unknown",
                source_section=item.source_section,
                confidence=item.confidence,
                agent="managing_agent"
            )
        # Convert ExtractedContent objects back to dicts for downstream steps
        content_dicts = [
            {**item.__dict__, "content_type": item.content_type.value if hasattr(item.content_type, 'value') else str(item.content_type)}
            for item in hydrated_content
        ]
        return {
            "initial_analysis": content_dicts,
            "confidence_scores": managing_results["confidence_scores"]
        }

    async def _run_gap_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run gap analysis on the initial analysis."""
        content = state["initial_analysis"]
        confidence_scores = state["confidence_scores"]
        # Analyze gaps
        gaps = self.gap_analyzer.analyze_documentation_gaps(
            content={item.get("title", ""): item.get("content", "") for item in content},
            confidence_scores=confidence_scores
        )
        # Generate gap report
        gap_report = self.gap_analyzer.generate_gap_report(gaps)
        # Generate SME questions
        sme_questions = []
        for gap in gaps:
            sme_questions.extend(gap.sme_questions)
        return {
            "gap_report": gap_report.dict(),
            "sme_questions": sme_questions
        }

    async def _run_review_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the review agent for validation and provenance checking."""
        from ai_doc_gen.agents.review_agent import ReviewAgent
        from ai_doc_gen.input_processing.structured_extractor import (
            ContentType,
            ExtractedContent,
        )
        initial_analysis = state["initial_analysis"]
        content = state["structured_content"]
        # Rehydrate dicts to ExtractedContent objects
        hydrated_content = []
        for item in content:
            if isinstance(item, dict):
                ct = item.get("content_type")
                if isinstance(ct, ContentType):
                    content_type = ct
                elif isinstance(ct, str):
                    content_type = ContentType(ct)
                else:
                    content_type = ContentType.NOTE
                hydrated_content.append(ExtractedContent(
                    content_type=content_type,
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    confidence=item.get("confidence", 0.0),
                    source_section=item.get("source_section", ""),
                    tags=item.get("tags", [])
                ))
            else:
                hydrated_content.append(item)
        review_agent = ReviewAgent()
        provenance_map = {item.title: f"{state['input_files'][0]}#{item.source_section}" for item in hydrated_content}
        review_results = review_agent.run(hydrated_content, provenance_map=provenance_map)
        # Attach validation results to each item
        validated_items = []
        for i, item in enumerate(initial_analysis):
            validated_item = item.copy()
            if i < len(review_results["audit_results"]):
                validated_item["validation"] = review_results["audit_results"][i]
            validated_items.append(validated_item)
        provenance_report = review_results.get("audit_results", [])
        return {
            "validated_analysis": validated_items,
            "provenance_report": provenance_report
        }

    async def _generate_draft(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final draft document in both JSON and Markdown formats."""
        validated_analysis = state["validated_analysis"]
        gap_report = state["gap_report"]

        # Generate draft content (JSON structure)
        draft_content = {
            "title": "Generated Hardware Documentation",
            "sections": [
                {
                    "heading": "Specifications",
                    "content": [
                        {
                            "spec_item": item.get("spec_item", ""),
                            "value": item.get("value", ""),
                            "confidence": item.get("confidence", "")
                        }
                        for item in validated_analysis
                    ]
                },
                {
                    "heading": "Gap Analysis Summary",
                    "content": [
                        f"Total gaps identified: {gap_report.get('total_gaps', 0)}",
                        f"Critical gaps: {gap_report.get('critical_gaps', 0)}",
                        f"Estimated resolution time: {gap_report.get('estimated_resolution_time', 'N/A')}"
                    ]
                },
                {
                    "heading": "SME Questions",
                    "content": gap_report.get("sme_questions", [])
                },
                {
                    "heading": "Recommendations",
                    "content": gap_report.get("recommended_actions", [])
                }
            ]
        }

        # Save draft to JSON file
        draft_file = Path(state["output_dir"]) / "generated_draft.json"
        with open(draft_file, 'w') as f:
            json.dump(draft_content, f, indent=2)

        # Generate Markdown
        def specs_table(specs):
            if not specs:
                return "_No specifications found._"
            header = "| Specification | Value | Confidence |\n|---|---|---|"
            rows = [
                f"| {s.get('spec_item','')} | {s.get('value','')} | {s.get('confidence','')}% |"
                for s in specs
            ]
            return '\n'.join([header] + rows)

        md_lines = [
            f"# {draft_content['title']}",
            "",
            "## Specifications",
            specs_table(draft_content['sections'][0]['content']),
            "",
            "## Gap Analysis Summary",
        ]
        for line in draft_content['sections'][1]['content']:
            md_lines.append(f"- {line}")
        md_lines.append("")
        md_lines.append("## SME Questions")
        sme_questions = draft_content['sections'][2]['content']
        if sme_questions:
            for q in sme_questions:
                if isinstance(q, dict):
                    md_lines.append(f"- **{q.get('priority','')}**: {q.get('question','')} (_{q.get('category','')}_)")
                else:
                    md_lines.append(f"- {q}")
        else:
            md_lines.append("_No SME questions generated._")
        md_lines.append("")
        md_lines.append("## Recommendations")
        recommendations = draft_content['sections'][3]['content']
        if recommendations:
            for rec in recommendations:
                md_lines.append(f"- {rec}")
        else:
            md_lines.append("_No recommendations._")
        md_content = '\n'.join(md_lines)

        # Save Markdown draft
        md_file = Path(state["output_dir"]) / "generated_draft.md"
        with open(md_file, 'w') as f:
            f.write(md_content)

        return {
            "draft_document": draft_content,
            "draft_markdown_file": str(md_file),
            "final_metrics": self.metrics.dict()
        }

    async def _generate_final_metrics(self, start_time: float) -> None:
        """Generate comprehensive final metrics."""
        end_time = time.time()
        duration = end_time - start_time

        self.metrics.pipeline_run = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "total_steps": len(self.steps),
            "successful_steps": len(self.steps) - len(self.error_log),
            "failed_steps": len(self.error_log)
        }

        # Calculate confidence metrics
        if "confidence_scores" in self.pipeline_state:
            scores = list(self.pipeline_state["confidence_scores"].values())
            self.metrics.confidence_metrics = {
                "average_confidence": self.confidence_scorer.calculate_average_confidence(scores),
                "min_confidence": min(scores) if scores else 0,
                "max_confidence": max(scores) if scores else 0,
                "total_items": len(scores)
            }

        # Calculate gap analysis metrics
        if "gap_report" in self.pipeline_state:
            gap_report = self.pipeline_state["gap_report"]
            self.metrics.gap_analysis_metrics = {
                "total_gaps": gap_report.get("total_gaps", 0),
                "critical_gaps": gap_report.get("critical_gaps", 0),
                "high_priority_gaps": gap_report.get("high_priority_gaps", 0),
                "estimated_resolution_time": gap_report.get("estimated_resolution_time", "N/A")
            }

    async def _save_pipeline_results(self) -> None:
        """Save pipeline results to output directory."""
        output_dir = Path(self.pipeline_state["output_dir"])

        # Save metrics
        metrics_file = output_dir / "pipeline_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics.dict(), f, indent=2)

        # Save provenance data
        provenance_file = output_dir / "provenance_data.json"
        self.provenance_tracker.export_provenance_data(str(provenance_file))

        # Save gap report
        if "gap_report" in self.pipeline_state:
            gap_file = output_dir / "gap_report.json"
            with open(gap_file, 'w') as f:
                json.dump(self.pipeline_state["gap_report"], f, indent=2)

        logger.info(f"Pipeline results saved to {output_dir}")

    async def _handle_pipeline_failure(self, error: Exception) -> None:
        """Handle pipeline failure and save error state with enum-safe serialization."""
        import json
        def enum_safe(obj):
            if isinstance(obj, dict):
                return {k: enum_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [enum_safe(i) for i in obj]
            elif hasattr(obj, 'value'):
                return obj.value
            return obj
        error_state = enum_safe(self.pipeline_state)
        error_state['error'] = str(error)
        with open("pipeline_error_state.json", "w") as f:
            json.dump(error_state, f, indent=2)
        logger.error(f"Pipeline failed: {error}")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        return {
            "current_step": self.current_step,
            "total_steps": len(self.steps),
            "pipeline_state": self.pipeline_state,
            "error_log": self.error_log,
            "metrics": self.metrics.dict()
        }
