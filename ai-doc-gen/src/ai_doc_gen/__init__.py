"""
AI-Assisted Hardware Documentation Generation System

A comprehensive system for generating hardware documentation using AI agents,
automated gap analysis, and provenance tracking.
"""

__version__ = "0.1.0"
__author__ = "AI Doc Gen Team"

from .core.confidence_scoring import ConfidenceScorer
from .core.llm_integration import LLMClient
from .core.pipeline_orchestrator import PipelineOrchestrator

__all__ = ["LLMClient", "ConfidenceScorer", "PipelineOrchestrator"]
