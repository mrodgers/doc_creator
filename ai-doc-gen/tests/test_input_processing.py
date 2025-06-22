"""
Tests for input processing module.

Tests document parsing, structured extraction, and validation functionality.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from ai_doc_gen.input_processing import (
    InputValidator,
    StructuredExtractor,
    extract_structured_content,
    parse_document,
    validate_document,
)
from ai_doc_gen.input_processing.document_parser import (
    DocumentParserFactory,
    DOCXParser,
    PDFParser,
    XMLParser,
)
from ai_doc_gen.input_processing.input_validator import (
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)
from ai_doc_gen.input_processing.structured_extractor import (
    ContentType,
    ExtractedContent,
)


class TestDocumentParser:
    """Test document parsing functionality."""

    def test_pdf_parser_initialization(self):
        """Test PDF parser initialization."""
        parser = PDFParser()
        assert parser is not None

    def test_docx_parser_initialization(self):
        """Test DOCX parser initialization."""
        parser = DOCXParser()
        assert parser is not None

    def test_xml_parser_initialization(self):
        """Test XML parser initialization."""
        parser = XMLParser()
        assert parser is not None

    def test_parser_factory_initialization(self):
        """Test parser factory initialization."""
        factory = DocumentParserFactory()
        assert factory is not None
        assert len(factory.parsers) > 0

    def test_parser_factory_supported_formats(self):
        """Test getting supported formats from factory."""
        factory = DocumentParserFactory()
        formats = factory.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0

    def test_can_parse_invalid_file(self):
        """Test can_parse with invalid file."""
        factory = DocumentParserFactory()
        parser = factory.get_parser("nonexistent.txt")
        assert parser is None

    @patch('ai_doc_gen.input_processing.document_parser.PDF_AVAILABLE', True)
    def test_pdf_parser_can_parse(self):
        """Test PDF parser can_parse method."""
        parser = PDFParser()
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_file = f.name
        try:
            assert parser.can_parse(temp_file) is True
            assert parser.can_parse("test.txt") is False
            assert parser.can_parse("nonexistent.pdf") is False
        finally:
            os.unlink(temp_file)

    @patch('ai_doc_gen.input_processing.document_parser.DOCX_AVAILABLE', True)
    def test_docx_parser_can_parse(self):
        """Test DOCX parser can_parse method."""
        parser = DOCXParser()
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        try:
            assert parser.can_parse(temp_file) is True
            assert parser.can_parse("test.txt") is False
        finally:
            os.unlink(temp_file)

    @patch('ai_doc_gen.input_processing.document_parser.XML_AVAILABLE', True)
    def test_xml_parser_can_parse(self):
        """Test XML parser can_parse method."""
        parser = XMLParser()
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
            temp_file = f.name
        try:
            assert parser.can_parse(temp_file) is True
            assert parser.can_parse("test.txt") is False
        finally:
            os.unlink(temp_file)


class TestStructuredExtractor:
    """Test structured content extraction."""

    def test_extractor_initialization(self):
        """Test structured extractor initialization."""
        extractor = StructuredExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'patterns')
        assert hasattr(extractor, 'keywords')

    def test_content_type_enum(self):
        """Test content type enumeration."""
        assert ContentType.TECHNICAL_SPEC.value == "technical_specification"
        assert ContentType.INSTALLATION_PROCEDURE.value == "installation_procedure"
        assert ContentType.REQUIREMENT.value == "requirement"

    def test_extracted_content_model(self):
        """Test extracted content model."""
        content = ExtractedContent(
            content_type=ContentType.TECHNICAL_SPEC,
            title="Test Spec",
            content="Test content",
            confidence=0.8,
            source_section="Test Section"
        )
        assert content.content_type == ContentType.TECHNICAL_SPEC
        assert content.title == "Test Spec"
        assert content.confidence == 0.8

    def test_classify_content_technical_spec(self):
        """Test content classification for technical specifications."""
        extractor = StructuredExtractor()

        text = "Technical Specifications: Dimensions 100mm x 200mm, Weight 2.5kg"
        result = extractor._classify_content(text, "Test Section")

        assert result is not None
        assert result.content_type == ContentType.TECHNICAL_SPEC
        assert result.confidence > 0.1

    def test_classify_content_installation(self):
        """Test content classification for installation procedures."""
        extractor = StructuredExtractor()

        text = "Installation Procedure: Step 1. Mount the device. Step 2. Connect cables."
        result = extractor._classify_content(text, "Test Section")

        assert result is not None
        assert result.content_type == ContentType.INSTALLATION_PROCEDURE
        assert result.confidence > 0.1

    def test_classify_content_warning(self):
        """Test content classification for warnings."""
        extractor = StructuredExtractor()

        text = "WARNING: Do not connect power while device is open."
        result = extractor._classify_content(text, "Test Section")

        assert result is not None
        assert result.content_type == ContentType.WARNING
        assert result.confidence > 0.1

    def test_extract_title(self):
        """Test title extraction."""
        extractor = StructuredExtractor()

        # Test with short title-like text
        text = "Installation Guide:\nThis is the content."
        title = extractor._extract_title(text)
        assert title == "Installation Guide:"

        # Test with long text
        text = "This is a very long text that should be truncated to create a title"
        title = extractor._extract_title(text)
        assert "..." in title
        assert len(title.split()) <= 5

    def test_extract_tags(self):
        """Test tag extraction."""
        extractor = StructuredExtractor()

        text = "Cisco router with 100V power supply and 1GB memory"
        tags = extractor._extract_tags(text, ContentType.TECHNICAL_SPEC)

        assert "cisco" in tags
        assert "100V" in tags
        assert "1GB" in tags

    def test_calculate_keyword_score(self):
        """Test keyword scoring."""
        extractor = StructuredExtractor()

        text = "The device has dimensions of 100mm x 200mm and weighs 2.5kg"
        score = extractor._calculate_keyword_score(text, ContentType.TECHNICAL_SPEC)

        assert score > 0.0

    def test_deduplicate_content(self):
        """Test content deduplication."""
        extractor = StructuredExtractor()

        # Create duplicate content items
        content1 = ExtractedContent(
            content_type=ContentType.TECHNICAL_SPEC,
            title="Test",
            content="Same content",
            confidence=0.8,
            source_section="Section 1"
        )
        content2 = ExtractedContent(
            content_type=ContentType.TECHNICAL_SPEC,
            title="Test",
            content="Same content",
            confidence=0.9,
            source_section="Section 2"
        )

        unique = extractor._deduplicate_content([content1, content2])
        assert len(unique) == 1

    def test_get_content_summary(self):
        """Test content summary generation."""
        extractor = StructuredExtractor()

        content_items = [
            ExtractedContent(
                content_type=ContentType.TECHNICAL_SPEC,
                title="Spec 1",
                content="Content 1",
                confidence=0.9,
                source_section="Section 1",
                tags=["cisco", "router"]
            ),
            ExtractedContent(
                content_type=ContentType.INSTALLATION_PROCEDURE,
                title="Install 1",
                content="Content 2",
                confidence=0.7,
                source_section="Section 2",
                tags=["install", "cable"]
            )
        ]

        summary = extractor.get_content_summary(content_items)

        assert summary['total_items'] == 2
        assert summary['content_types']['technical_specification'] == 1
        assert summary['content_types']['installation_procedure'] == 1
        assert summary['confidence_distribution']['high'] == 1
        assert summary['confidence_distribution']['medium'] == 1


class TestInputValidator:
    """Test input validation functionality."""

    def test_validator_initialization(self):
        """Test input validator initialization."""
        validator = InputValidator()
        assert validator is not None
        assert validator.min_file_size > 0
        assert validator.max_file_size > validator.min_file_size

    def test_validation_level_enum(self):
        """Test validation level enumeration."""
        assert ValidationLevel.INFO.value == "info"
        assert ValidationLevel.WARNING.value == "warning"
        assert ValidationLevel.ERROR.value == "error"
        assert ValidationLevel.CRITICAL.value == "critical"

    def test_validation_issue_model(self):
        """Test validation issue model."""
        issue = ValidationIssue(
            level=ValidationLevel.WARNING,
            message="Test warning",
            field="test_field",
            suggestion="Test suggestion"
        )
        assert issue.level == ValidationLevel.WARNING
        assert issue.message == "Test warning"
        assert issue.suggestion == "Test suggestion"

    def test_validation_result_model(self):
        """Test validation result model."""
        result = ValidationResult(
            is_valid=True,
            score=0.8,
            issues=[],
            warnings=[],
            recommendations=[]
        )
        assert result.is_valid is True
        assert result.score == 0.8

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        validator = InputValidator()
        result = validator.validate_document("nonexistent.pdf")

        assert result.is_valid is False
        assert result.score < 0.6
        assert len(result.issues) > 0
        assert any(issue.level == ValidationLevel.CRITICAL for issue in result.issues)

    def test_validate_unsupported_extension(self):
        """Test validation of unsupported file extension."""
        validator = InputValidator()
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_file = f.name
        try:
            result = validator.validate_document(temp_file)
            assert result.is_valid is False
            assert len(result.issues) > 0
            assert any(issue.field == "file_extension" for issue in result.issues)
        finally:
            os.unlink(temp_file)

    def test_validate_file_size(self):
        """Test file size validation."""
        validator = InputValidator()

        # Create a temporary file that's too small
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"x" * 100)  # 100 bytes, below minimum
            temp_file = f.name

        try:
            result = validator.validate_document(temp_file)
            assert len(result.issues) > 0
            assert any(issue.field == "file_size" for issue in result.issues)
        finally:
            os.unlink(temp_file)

    def test_calculate_duplicate_ratio(self):
        """Test duplicate ratio calculation."""
        validator = InputValidator()

        # Text with duplicates
        text = "Line 1\nLine 2\nLine 1\nLine 3\nLine 2"
        ratio = validator._calculate_duplicate_ratio(text)

        assert ratio > 0.0
        assert ratio <= 1.0

    def test_calculate_score(self):
        """Test validation score calculation."""
        validator = InputValidator()

        # Test with no issues
        score = validator._calculate_score([])
        assert score == 1.0

        # Test with different issue levels
        issues = [
            ValidationIssue(level=ValidationLevel.INFO, message="Info"),
            ValidationIssue(level=ValidationLevel.WARNING, message="Warning"),
            ValidationIssue(level=ValidationLevel.ERROR, message="Error")
        ]

        score = validator._calculate_score(issues)
        assert score < 1.0
        assert score > 0.0

    def test_generate_warnings(self):
        """Test warning generation."""
        validator = InputValidator()

        issues = [
            ValidationIssue(level=ValidationLevel.INFO, message="Info"),
            ValidationIssue(level=ValidationLevel.WARNING, message="Warning", suggestion="Fix it"),
            ValidationIssue(level=ValidationLevel.ERROR, message="Error")
        ]

        warnings = validator._generate_warnings(issues)
        assert len(warnings) == 2  # Warning and Error, not Info
        assert any("Fix it" in warning for warning in warnings)

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        validator = InputValidator()

        issues = [
            ValidationIssue(level=ValidationLevel.ERROR, message="File error", field="file_path"),
            ValidationIssue(level=ValidationLevel.WARNING, message="Content warning", field="content")
        ]

        recommendations = validator._generate_recommendations(issues)
        assert len(recommendations) > 0
        assert any("file" in rec.lower() for rec in recommendations)
        assert any("content" in rec.lower() for rec in recommendations)


class TestIntegration:
    """Integration tests for input processing."""

    def test_parse_document_convenience_function(self):
        """Test parse_document convenience function."""
        # This would require a real file, so we'll test the function exists
        assert callable(parse_document)

    def test_extract_structured_content_convenience_function(self):
        """Test extract_structured_content convenience function."""
        assert callable(extract_structured_content)

    def test_validate_document_convenience_function(self):
        """Test validate_document convenience function."""
        assert callable(validate_document)

    def test_end_to_end_processing(self):
        """Test end-to-end processing workflow."""
        # Create a mock parsed document
        mock_doc = Mock()
        mock_doc.raw_text = "Technical Specifications: Dimensions 100mm x 200mm. Installation: Mount the device."
        mock_doc.sections = [
            {
                'heading': 'Technical Specs',
                'content': ['Dimensions: 100mm x 200mm', 'Weight: 2.5kg'],
                'level': 1
            },
            {
                'heading': 'Installation',
                'content': ['Step 1: Mount device', 'Step 2: Connect cables'],
                'level': 1
            }
        ]
        mock_doc.parsing_errors = []

        # Test structured extraction
        extractor = StructuredExtractor()
        extracted = extractor.extract_structured_content(mock_doc)

        assert len(extracted) > 0
        assert any(item.content_type == ContentType.TECHNICAL_SPEC for item in extracted)
        assert any(item.content_type == ContentType.INSTALLATION_PROCEDURE for item in extracted)

        # Test content summary
        summary = extractor.get_content_summary(extracted)
        assert summary['total_items'] > 0
        assert 'technical_specification' in summary['content_types']
        assert 'installation_procedure' in summary['content_types']


if __name__ == "__main__":
    pytest.main([__file__])
