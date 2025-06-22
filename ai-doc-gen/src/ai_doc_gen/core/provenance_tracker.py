"""
Provenance Tracking Module

Based on the original audit_specs.py but enhanced for comprehensive provenance tracking
across the multi-agent documentation generation system.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

@dataclass
class ProvenanceEntry:
    """Individual provenance entry with metadata."""
    source_document: str
    source_section: str
    extracted_value: str
    confidence: float
    timestamp: str
    agent: str
    context: str
    validation_status: str = "pending"
    validation_notes: Optional[str] = None

class ProvenanceRecord(BaseModel):
    """Complete provenance record for a piece of information."""
    item_id: str
    item_type: str
    value: str
    confidence: float = Field(ge=0, le=100)
    sources: List[ProvenanceEntry]
    validation_history: List[Dict[str, Any]]
    last_updated: str
    status: str = "active"

class ProvenanceTracker:
    """Enhanced provenance tracking system for multi-agent architecture."""

    def __init__(self):
        """Initialize provenance tracker."""
        self.provenance_records: Dict[str, ProvenanceRecord] = {}
        self.source_documents: Set[str] = set()
        self.validation_rules: Dict[str, Any] = {}

    def add_provenance_entry(
        self,
        item_id: str,
        item_type: str,
        value: str,
        source_document: str,
        source_section: str,
        confidence: float,
        agent: str,
        context: str = ""
    ) -> None:
        """Add a new provenance entry for tracking information sources."""

        entry = ProvenanceEntry(
            source_document=source_document,
            source_section=source_section,
            extracted_value=value,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            agent=agent,
            context=context
        )

        if item_id not in self.provenance_records:
            # Create new provenance record
            self.provenance_records[item_id] = ProvenanceRecord(
                item_id=item_id,
                item_type=item_type,
                value=value,
                confidence=confidence,
                sources=[entry],
                validation_history=[],
                last_updated=entry.timestamp,
                status="active"
            )
        else:
            # Update existing record
            record = self.provenance_records[item_id]
            record.sources.append(entry)
            record.value = value  # Update with latest value
            record.confidence = confidence
            record.last_updated = entry.timestamp

        # Track source document
        self.source_documents.add(source_document)

        logger.info(f"Added provenance entry for {item_id} from {source_document}")

    def validate_provenance(
        self,
        item_id: str,
        original_content: Dict[str, Any],
        validation_agent: str = "review_agent"
    ) -> Dict[str, Any]:
        """Validate provenance by cross-referencing with original content."""

        if item_id not in self.provenance_records:
            return {"status": "error", "message": f"No provenance record found for {item_id}"}

        record = self.provenance_records[item_id]
        validation_result = {
            "item_id": item_id,
            "validation_agent": validation_agent,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "issues": [],
            "confidence_adjustment": 0
        }

        # Validate each source
        for source in record.sources:
            source_validation = self._validate_source(source, original_content)
            if source_validation["status"] != "valid":
                validation_result["issues"].append(source_validation)
                validation_result["confidence_adjustment"] -= 10

        # Determine overall validation status
        if not validation_result["issues"]:
            validation_result["status"] = "valid"
            validation_result["confidence_adjustment"] = 5  # Bonus for validation
        elif len(validation_result["issues"]) <= 2:
            validation_result["status"] = "warning"
        else:
            validation_result["status"] = "invalid"

        # Update confidence based on validation
        record.confidence = max(0, min(100, record.confidence + validation_result["confidence_adjustment"]))

        # Add to validation history
        record.validation_history.append(validation_result)

        return validation_result

    def _validate_source(
        self,
        source: ProvenanceEntry,
        original_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single source against original content."""

        # Flatten all content for searching
        all_content = []
        for section in original_content.get('sections', []):
            all_content.extend(section.get('content', []))

        full_text = " ".join(all_content)

        # Check if the extracted value exists in the source
        normalized_value = re.sub(r'[^a-zA-Z0-9]', '', source.extracted_value.lower())
        normalized_text = re.sub(r'[^a-zA-Z0-9]', '', full_text.lower())

        if normalized_value in normalized_text:
            return {
                "source": source.source_document,
                "status": "valid",
                "message": "Value found in source document"
            }
        else:
            # Try fuzzy matching for specific patterns
            snippet = self._find_specific_snippet(source.extracted_value, full_text)
            if snippet:
                return {
                    "source": source.source_document,
                    "status": "warning",
                    "message": f"Value found with context: {snippet[:100]}...",
                    "snippet": snippet
                }
            else:
                return {
                    "source": source.source_document,
                    "status": "invalid",
                    "message": "Value not found in source document"
                }

    def _find_specific_snippet(self, value: str, full_text: str) -> Optional[str]:
        """Find specific snippet containing the value with context."""

        # Define patterns for common hardware specifications
        spec_patterns = {
            "QSFP port count": [
                r"64.*QSFP", r"64100-GigabitQSFP", r"64.*100-Gigabit.*QSFP",
                r"64100GigabitQSFP", r"64.*QSFP.*port"
            ],
            "Management ports": [
                r"Two.*management.*port", r"2.*management.*port", r"management.*port.*2",
                r"RJ-45.*port.*SFP.*port", r"one.*RJ-45.*port.*one.*SFP.*port"
            ],
            "Chassis dimensions": [
                r"17\.41.*inches", r"22\.27.*inches", r"3\.4.*inches",
                r"Width.*17\.41", r"Depth.*22\.27", r"Height.*3\.4"
            ],
            "Power requirements": [
                r"605W.*1100W", r"605W.*typical", r"power.*input.*605W",
                r"4248.*BTU", r"heat.*dissipation.*4248"
            ]
        }

        # Try to match value against patterns
        for spec_type, patterns in spec_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 150)
                    end = min(len(full_text), match.end() + 150)
                    return full_text[start:end]

        return None

    def get_provenance_report(self, item_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive provenance report."""

        if item_id:
            if item_id not in self.provenance_records:
                return {"error": f"No provenance record found for {item_id}"}

            record = self.provenance_records[item_id]
            return {
                "item_id": item_id,
                "provenance": asdict(record),
                "validation_summary": self._summarize_validation(record.validation_history)
            }

        # Generate overall report
        total_items = len(self.provenance_records)
        total_sources = sum(len(record.sources) for record in self.provenance_records.values())

        # Calculate confidence statistics
        confidences = [record.confidence for record in self.provenance_records.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Count validation statuses
        validation_counts = {"valid": 0, "warning": 0, "invalid": 0, "pending": 0}
        for record in self.provenance_records.values():
            if record.validation_history:
                latest_validation = record.validation_history[-1]
                status = latest_validation.get("status", "pending")
                validation_counts[status] += 1
            else:
                validation_counts["pending"] += 1

        return {
            "summary": {
                "total_items": total_items,
                "total_sources": total_sources,
                "average_confidence": round(avg_confidence, 2),
                "source_documents": list(self.source_documents),
                "validation_counts": validation_counts
            },
            "items": {
                item_id: {
                    "type": record.item_type,
                    "value": record.value,
                    "confidence": record.confidence,
                    "sources_count": len(record.sources),
                    "last_updated": record.last_updated,
                    "status": record.status
                }
                for item_id, record in self.provenance_records.items()
            }
        }

    def _summarize_validation(self, validation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize validation history for a record."""
        if not validation_history:
            return {"status": "pending", "total_validations": 0}

        latest_validation = validation_history[-1]
        return {
            "status": latest_validation.get("status", "pending"),
            "total_validations": len(validation_history),
            "latest_agent": latest_validation.get("validation_agent", "unknown"),
            "latest_timestamp": latest_validation.get("timestamp", ""),
            "issues_count": len(latest_validation.get("issues", []))
        }

    def export_provenance_data(self, filepath: str) -> None:
        """Export all provenance data to JSON file."""
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_records": len(self.provenance_records),
                "source_documents": list(self.source_documents)
            },
            "provenance_records": {
                item_id: record.dict() for item_id, record in self.provenance_records.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Provenance data exported to {filepath}")

    def import_provenance_data(self, filepath: str) -> None:
        """Import provenance data from JSON file."""
        with open(filepath) as f:
            import_data = json.load(f)

        # Import provenance records
        for item_id, record_data in import_data.get("provenance_records", {}).items():
            self.provenance_records[item_id] = ProvenanceRecord(**record_data)

        # Import source documents
        self.source_documents.update(import_data.get("metadata", {}).get("source_documents", []))

        logger.info(f"Provenance data imported from {filepath}")

    def get_source_analysis(self) -> Dict[str, Any]:
        """Analyze source document usage and reliability."""
        source_stats = {}

        for record in self.provenance_records.values():
            for source in record.sources:
                if source.source_document not in source_stats:
                    source_stats[source.source_document] = {
                        "usage_count": 0,
                        "total_confidence": 0,
                        "validation_success_rate": 0,
                        "sections_used": set()
                    }

                stats = source_stats[source.source_document]
                stats["usage_count"] += 1
                stats["total_confidence"] += source.confidence
                stats["sections_used"].add(source.source_section)

        # Calculate averages and convert sets to lists
        for source, stats in source_stats.items():
            stats["average_confidence"] = stats["total_confidence"] / stats["usage_count"]
            stats["sections_used"] = list(stats["sections_used"])
            del stats["total_confidence"]  # Remove intermediate calculation

        return {
            "source_documents": source_stats,
            "total_sources": len(source_stats),
            "most_used_source": max(source_stats.keys(), key=lambda x: source_stats[x]["usage_count"]) if source_stats else None
        }
