"""
Input Validator

Validates input documents for quality, completeness, and suitability
for AI processing. Ensures documents meet minimum standards before
processing to improve AI output quality.
"""

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationIssue(BaseModel):
    """Represents a validation issue found in a document."""
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None
    line_number: Optional[int] = None

class ValidationResult(BaseModel):
    """Result of document validation."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    issues: List[ValidationIssue] = []
    warnings: List[str] = []
    recommendations: List[str] = []

class InputValidator:
    """Validates input documents for AI processing suitability."""

    def __init__(self):
        """Initialize validator with thresholds and rules."""
        self.min_file_size = 1024  # 1KB minimum
        self.max_file_size = 50 * 1024 * 1024  # 50MB maximum
        self.min_text_length = 100  # Minimum characters
        self.max_text_length = 1000000  # 1M characters maximum
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.xml', '.txt', '.html'}

        # Quality thresholds
        self.min_sections = 2
        self.min_content_ratio = 0.1  # 10% of text should be content
        self.max_duplicate_ratio = 0.3  # Max 30% duplicate content

    def validate_document(self, file_path: str,
                         parsed_document=None) -> ValidationResult:
        """Validate a document file and its parsed content."""
        result = ValidationResult(
            is_valid=True,
            score=1.0,
            issues=[],
            warnings=[],
            recommendations=[]
        )

        # File-level validation
        file_issues = self._validate_file(file_path)
        result.issues.extend(file_issues)

        # Content validation if parsed document provided
        if parsed_document:
            content_issues = self._validate_content(parsed_document)
            result.issues.extend(content_issues)

        # Calculate overall score and validity
        result.score = self._calculate_score(result.issues)
        result.is_valid = result.score >= 0.6  # Minimum 60% score

        # Generate warnings and recommendations
        result.warnings = self._generate_warnings(result.issues)
        result.recommendations = self._generate_recommendations(result.issues)

        return result

    def _validate_file(self, file_path: str) -> List[ValidationIssue]:
        """Validate file-level properties."""
        issues = []
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"File does not exist: {file_path}",
                field="file_path"
            ))
            return issues

        # Check file extension
        if path.suffix.lower() not in self.supported_extensions:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Unsupported file type: {path.suffix}",
                field="file_extension",
                suggestion=f"Supported types: {', '.join(self.supported_extensions)}"
            ))

        # Check file size
        try:
            file_size = path.stat().st_size
            if file_size < self.min_file_size:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"File is very small ({file_size} bytes)",
                    field="file_size",
                    suggestion="File may not contain sufficient content for processing"
                ))
            elif file_size > self.max_file_size:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"File is too large ({file_size} bytes)",
                    field="file_size",
                    suggestion=f"Maximum supported size: {self.max_file_size} bytes"
                ))
        except OSError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Cannot access file: {e}",
                field="file_access"
            ))

        # Check file permissions
        try:
            if not os.access(file_path, os.R_OK):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="File is not readable",
                    field="file_permissions",
                    suggestion="Check file permissions"
                ))
        except OSError:
            pass  # Already handled above

        return issues

    def _validate_content(self, parsed_document) -> List[ValidationIssue]:
        """Validate parsed document content."""
        issues = []

        # Check text length
        text_length = len(parsed_document.raw_text)
        if text_length < self.min_text_length:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Document too short ({text_length} characters)",
                field="text_length",
                suggestion=f"Minimum required: {self.min_text_length} characters"
            ))
        elif text_length > self.max_text_length:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Document very long ({text_length} characters)",
                field="text_length",
                suggestion="Consider splitting into smaller documents"
            ))

        # Check for sections
        if len(parsed_document.sections) < self.min_sections:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Document has few sections ({len(parsed_document.sections)})",
                field="sections",
                suggestion="Documents with clear structure produce better results"
            ))

        # Check content quality
        quality_issues = self._check_content_quality(parsed_document)
        issues.extend(quality_issues)

        # Check for parsing errors
        if parsed_document.parsing_errors:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Document had {len(parsed_document.parsing_errors)} parsing issues",
                field="parsing",
                suggestion="Some content may not have been extracted properly"
            ))

        return issues

    def _check_content_quality(self, parsed_document) -> List[ValidationIssue]:
        """Check content quality metrics."""
        issues = []
        text = parsed_document.raw_text

        # Check for empty or whitespace-only content
        if not text.strip():
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="Document contains no readable text",
                field="content",
                suggestion="Ensure document contains extractable text content"
            ))
            return issues

        # Check content ratio (non-whitespace characters)
        content_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        total_chars = len(text)
        content_ratio = content_chars / total_chars if total_chars > 0 else 0

        if content_ratio < self.min_content_ratio:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Low content density ({content_ratio:.1%})",
                field="content_quality",
                suggestion="Document may contain mostly formatting or whitespace"
            ))

        # Check for duplicate content
        duplicate_ratio = self._calculate_duplicate_ratio(text)
        if duplicate_ratio > self.max_duplicate_ratio:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"High duplicate content ({duplicate_ratio:.1%})",
                field="content_quality",
                suggestion="Consider removing duplicate sections"
            ))

        # Check for common quality issues
        quality_issues = self._check_common_issues(text)
        issues.extend(quality_issues)

        return issues

    def _calculate_duplicate_ratio(self, text: str) -> float:
        """Calculate the ratio of duplicate content."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return 0.0

        # Count duplicate lines
        seen_lines = set()
        duplicates = 0

        for line in lines:
            if line in seen_lines:
                duplicates += 1
            else:
                seen_lines.add(line)

        return duplicates / len(lines) if lines else 0.0

    def _check_common_issues(self, text: str) -> List[ValidationIssue]:
        """Check for common document quality issues."""
        issues = []

        # Check for excessive whitespace
        consecutive_newlines = text.count('\n\n\n')
        if consecutive_newlines > 10:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Document contains excessive whitespace",
                field="formatting",
                suggestion="Consider cleaning up formatting"
            ))

        # Check for very long lines
        lines = text.split('\n')
        long_lines = sum(1 for line in lines if len(line) > 200)
        if long_lines > len(lines) * 0.1:  # More than 10% long lines
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Document contains many very long lines",
                field="formatting",
                suggestion="Consider breaking long lines for better readability"
            ))

        # Check for encoding issues
        if '' in text or '\x00' in text:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Document may have encoding issues",
                field="encoding",
                suggestion="Check document encoding and re-save if necessary"
            ))

        # Check for placeholder text
        placeholder_patterns = [
            r'lorem\s+ipsum',
            r'placeholder',
            r'sample\s+text',
            r'\[.*?\]',  # Bracketed placeholders
            r'\{.*?\}',  # Braced placeholders
        ]

        import re
        for pattern in placeholder_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="Document contains placeholder text",
                    field="content",
                    suggestion="Replace placeholder text with actual content"
                ))
                break

        return issues

    def _calculate_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate overall validation score."""
        if not issues:
            return 1.0

        # Weight issues by severity
        weights = {
            ValidationLevel.INFO: 0.05,
            ValidationLevel.WARNING: 0.15,
            ValidationLevel.ERROR: 0.4,
            ValidationLevel.CRITICAL: 0.8
        }

        total_penalty = 0.0
        for issue in issues:
            penalty = weights.get(issue.level, 0.1)
            total_penalty += penalty

        # Cap penalty at 1.0
        total_penalty = min(total_penalty, 1.0)

        return max(0.0, 1.0 - total_penalty)

    def _generate_warnings(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate user-friendly warnings from issues."""
        warnings = []

        for issue in issues:
            if issue.level in [ValidationLevel.WARNING, ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
                warning = issue.message
                if issue.suggestion:
                    warning += f" - {issue.suggestion}"
                warnings.append(warning)

        return warnings

    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate actionable recommendations from issues."""
        recommendations = []

        # Group issues by type
        file_issues = [i for i in issues if i.field in ['file_path', 'file_size', 'file_extension']]
        content_issues = [i for i in issues if i.field in ['content', 'text_length', 'sections']]
        quality_issues = [i for i in issues if i.field in ['content_quality', 'formatting', 'encoding']]

        # File-related recommendations
        if file_issues:
            recommendations.append("Review file format and size requirements")

        # Content-related recommendations
        if content_issues:
            recommendations.append("Ensure document has sufficient content and structure")

        # Quality-related recommendations
        if quality_issues:
            recommendations.append("Clean up document formatting and remove placeholders")

        # General recommendations
        if len(issues) > 5:
            recommendations.append("Consider using a different document or improving document quality")

        return list(set(recommendations))  # Remove duplicates

    def validate_batch(self, file_paths: List[str]) -> Dict[str, ValidationResult]:
        """Validate multiple documents and return results."""
        results = {}

        for file_path in file_paths:
            try:
                result = self.validate_document(file_path)
                results[file_path] = result
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                results[file_path] = ValidationResult(
                    is_valid=False,
                    score=0.0,
                    issues=[ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        message=f"Validation failed: {e}",
                        field="validation_error"
                    )]
                )

        return results

    def get_validation_summary(self, results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Generate summary of batch validation results."""
        summary = {
            'total_files': len(results),
            'valid_files': sum(1 for r in results.values() if r.is_valid),
            'average_score': 0.0,
            'issues_by_level': {
                'info': 0,
                'warning': 0,
                'error': 0,
                'critical': 0
            },
            'common_issues': {},
            'recommendations': set()
        }

        if not results:
            return summary

        # Calculate statistics
        total_score = sum(r.score for r in results.values())
        summary['average_score'] = total_score / len(results)

        # Count issues by level
        for result in results.values():
            for issue in result.issues:
                level = issue.level.value
                summary['issues_by_level'][level] += 1

                # Track common issues
                issue_key = f"{issue.field}: {issue.message[:50]}"
                summary['common_issues'][issue_key] = summary['common_issues'].get(issue_key, 0) + 1

            # Collect recommendations
            summary['recommendations'].update(result.recommendations)

        # Convert set to list for JSON serialization
        summary['recommendations'] = list(summary['recommendations'])

        # Sort common issues by frequency
        summary['common_issues'] = dict(
            sorted(summary['common_issues'].items(),
                  key=lambda x: x[1], reverse=True)[:10]
        )

        return summary

# Convenience functions
def validate_document(file_path: str, parsed_document=None) -> ValidationResult:
    """Validate a single document."""
    validator = InputValidator()
    return validator.validate_document(file_path, parsed_document)

def validate_batch(file_paths: List[str]) -> Dict[str, ValidationResult]:
    """Validate multiple documents."""
    validator = InputValidator()
    return validator.validate_batch(file_paths)
