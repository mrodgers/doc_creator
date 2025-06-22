"""
Document Parser Module

Handles parsing of various document formats (PDF, DOCX, XML) and extracts
structured content for AI processing. Based on patterns from the original
codebase but enhanced for multi-format support.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod
import json
from pydantic import BaseModel

# PDF processing
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("pdfplumber not available - PDF parsing disabled")

# DOCX processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available - DOCX parsing disabled")

# XML processing
try:
    import xml.etree.ElementTree as ET
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False
    logging.warning("xml.etree not available - XML parsing disabled")

# HTML processing
try:
    from bs4 import BeautifulSoup
    import pandas as pd
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    logging.warning("beautifulsoup4 or pandas not available - HTML parsing disabled")

logger = logging.getLogger(__name__)

class ParsedDocument(BaseModel):
    """Structured representation of a parsed document."""
    filename: str
    file_type: str
    title: Optional[str] = None
    sections: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    raw_text: str = ""
    parsing_errors: List[str] = []

class DocumentParser(ABC):
    """Abstract base class for document parsers."""
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file."""
        pass
    
    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse the document and return structured content."""
        pass
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from the document."""
        pass

class PDFParser(DocumentParser):
    """PDF document parser using pdfplumber."""
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a PDF."""
        return (PDF_AVAILABLE and 
                Path(file_path).suffix.lower() == '.pdf' and 
                Path(file_path).exists())
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse PDF document and extract structured content."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        filename = Path(file_path).name
        parsed_doc = ParsedDocument(
            filename=filename,
            file_type="pdf",
            sections=[],
            metadata={},
            raw_text="",
            parsing_errors=[]
        )
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract metadata
                parsed_doc.metadata = {
                    "pages": len(pdf.pages),
                    "title": pdf.metadata.get('Title', ''),
                    "author": pdf.metadata.get('Author', ''),
                    "subject": pdf.metadata.get('Subject', ''),
                    "creator": pdf.metadata.get('Creator', ''),
                    "producer": pdf.metadata.get('Producer', '')
                }
                
                # Extract text from each page
                all_text = []
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            all_text.append(page_text)
                            
                            # Try to identify sections based on headers
                            section = self._identify_section(page_text, page_num)
                            if section:
                                parsed_doc.sections.append(section)
                                
                    except Exception as e:
                        error_msg = f"Error parsing page {page_num}: {e}"
                        parsed_doc.parsing_errors.append(error_msg)
                        logger.warning(error_msg)
                
                parsed_doc.raw_text = "\n".join(all_text)
                
                # Extract title if not in metadata
                if not parsed_doc.metadata.get('title'):
                    parsed_doc.title = self._extract_title(parsed_doc.raw_text)
                
        except Exception as e:
            error_msg = f"Error parsing PDF {file_path}: {e}"
            parsed_doc.parsing_errors.append(error_msg)
            logger.error(error_msg)
        
        return parsed_doc
    
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from PDF."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    def _identify_section(self, page_text: str, page_num: int) -> Optional[Dict[str, Any]]:
        """Identify sections based on text patterns."""
        lines = page_text.split('\n')
        
        # Look for common header patterns
        for i, line in enumerate(lines):
            line = line.strip()
            if self._is_header(line):
                # Extract section content
                content = lines[i+1:i+20]  # Next 20 lines as content
                return {
                    "heading": line,
                    "level": self._get_header_level(line),
                    "content": [l.strip() for l in content if l.strip()],
                    "page": page_num,
                    "start_line": i
                }
        
        return None
    
    def _is_header(self, line: str) -> bool:
        """Check if a line looks like a header."""
        if not line:
            return False
        
        # Common header patterns
        header_patterns = [
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS
            r'^\d+\.\s+[A-Z]',   # Numbered sections
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$',  # Title Case
            r'^Chapter\s+\d+',   # Chapter headers
            r'^Section\s+\d+',   # Section headers
        ]
        
        import re
        for pattern in header_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _get_header_level(self, header: str) -> int:
        """Determine header level based on formatting."""
        if header.isupper():
            return 1  # Main heading
        elif header.startswith(('Chapter', 'Section')):
            return 2  # Chapter/Section
        elif any(char.isdigit() for char in header):
            return 3  # Numbered subsection
        else:
            return 4  # Subheading
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract document title from text."""
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) > 5 and len(line) < 100:
                # Simple heuristic: first substantial line might be title
                return line
        return None

class DOCXParser(DocumentParser):
    """DOCX document parser using python-docx."""
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a DOCX."""
        return (DOCX_AVAILABLE and 
                Path(file_path).suffix.lower() in ['.docx', '.doc'] and 
                Path(file_path).exists())
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse DOCX document and extract structured content."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        filename = Path(file_path).name
        parsed_doc = ParsedDocument(
            filename=filename,
            file_type="docx",
            sections=[],
            metadata={},
            raw_text="",
            parsing_errors=[]
        )
        
        try:
            doc = Document(file_path)
            
            # Extract metadata
            core_props = doc.core_properties
            parsed_doc.metadata = {
                "title": core_props.title or "",
                "author": core_props.author or "",
                "subject": core_props.subject or "",
                "created": str(core_props.created) if core_props.created else "",
                "modified": str(core_props.modified) if core_props.modified else "",
                "paragraphs": len(doc.paragraphs)
            }
            
            # Extract content
            sections = []
            current_section = None
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                # Check if this is a heading
                if self._is_heading(para):
                    # Save previous section
                    if current_section:
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        "heading": text,
                        "level": self._get_heading_level(para),
                        "content": [],
                        "page": 1  # DOCX doesn't have page info easily
                    }
                else:
                    # Add to current section
                    if current_section:
                        current_section["content"].append(text)
                    else:
                        # No section yet, might be title
                        if not parsed_doc.title:
                            parsed_doc.title = text
            
            # Add final section
            if current_section:
                sections.append(current_section)
            
            parsed_doc.sections = sections
            parsed_doc.raw_text = self.extract_text(file_path)
            
        except Exception as e:
            error_msg = f"Error parsing DOCX {file_path}: {e}"
            parsed_doc.parsing_errors.append(error_msg)
            logger.error(error_msg)
        
        return parsed_doc
    
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from DOCX."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        try:
            doc = Document(file_path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            raise
    
    def _is_heading(self, paragraph) -> bool:
        """Check if paragraph is a heading."""
        # Check paragraph style
        if paragraph.style.name.startswith('Heading'):
            return True
        
        # Check if text looks like a heading
        text = paragraph.text.strip()
        if not text:
            return False
        
        # Simple heuristics
        if text.isupper() and len(text) < 100:
            return True
        
        if any(char.isdigit() for char in text) and len(text) < 50:
            return True
        
        return False
    
    def _get_heading_level(self, paragraph) -> int:
        """Get heading level from paragraph style."""
        style_name = paragraph.style.name
        if 'Heading' in style_name:
            # Extract number from style name
            import re
            match = re.search(r'Heading\s*(\d+)', style_name)
            if match:
                return int(match.group(1))
        
        # Default level based on text characteristics
        text = paragraph.text.strip()
        if text.isupper():
            return 1
        elif any(char.isdigit() for char in text):
            return 2
        else:
            return 3

class XMLParser(DocumentParser):
    """XML document parser using ElementTree."""
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is an XML."""
        return (XML_AVAILABLE and 
                Path(file_path).suffix.lower() == '.xml' and 
                Path(file_path).exists())
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse XML document and extract structured content."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        filename = Path(file_path).name
        parsed_doc = ParsedDocument(
            filename=filename,
            file_type="xml",
            sections=[],
            metadata={},
            raw_text="",
            parsing_errors=[]
        )
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract metadata from root attributes
            parsed_doc.metadata = dict(root.attrib)
            
            # Extract title
            title_elem = root.find('.//title')
            if title_elem is not None:
                parsed_doc.title = title_elem.text
            
            # Extract sections
            sections = []
            for section_elem in root.findall('.//section'):
                section = self._parse_section_element(section_elem)
                if section:
                    sections.append(section)
            
            parsed_doc.sections = sections
            parsed_doc.raw_text = self.extract_text(file_path)
            
        except Exception as e:
            error_msg = f"Error parsing XML {file_path}: {e}"
            parsed_doc.parsing_errors.append(error_msg)
            logger.error(error_msg)
        
        return parsed_doc
    
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from XML."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract all text content
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from XML {file_path}: {e}")
            raise
    
    def _parse_section_element(self, section_elem) -> Optional[Dict[str, Any]]:
        """Parse a section element and extract structured content."""
        try:
            # Extract heading
            heading_elem = section_elem.find('heading')
            if heading_elem is None:
                return None
            
            heading = heading_elem.text.strip() if heading_elem.text else ""
            
            # Extract content
            content_elem = section_elem.find('content')
            content = []
            if content_elem is not None and content_elem.text:
                content = [line.strip() for line in content_elem.text.split('\n') if line.strip()]
            
            return {
                "heading": heading,
                "level": 1,  # Default level for XML sections
                "content": content,
                "source": "xml"
            }
        except Exception as e:
            logger.warning(f"Error parsing XML section: {e}")
            return None

class HTMLParser(DocumentParser):
    """HTML document parser using BeautifulSoup."""
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is an HTML file."""
        return (HTML_AVAILABLE and 
                Path(file_path).suffix.lower() in ['.html', '.htm'] and 
                Path(file_path).exists())
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse HTML document and extract structured content using enhanced scraping methods."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        filename = Path(file_path).name
        parsed_doc = ParsedDocument(
            filename=filename,
            file_type="html",
            sections=[],
            metadata={},
            raw_text="",
            parsing_errors=[]
        )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract metadata
            parsed_doc.metadata = {
                "title": soup.title.string if soup.title else "",
                "language": soup.get('lang', ''),
                "charset": soup.meta.get('charset', '') if soup.meta else "",
                "description": soup.find('meta', {'name': 'description'}).get('content', '') if soup.find('meta', {'name': 'description'}) else ""
            }
            
            # Extract title
            if soup.title:
                parsed_doc.title = soup.title.string.strip()
            
            # Extract sections using enhanced methods
            sections = self._extract_enhanced_sections(soup)
            parsed_doc.sections = sections
            
            # Extract raw text
            parsed_doc.raw_text = self._extract_clean_text(soup)
            
        except Exception as e:
            error_msg = f"Error parsing HTML {file_path}: {e}"
            parsed_doc.parsing_errors.append(error_msg)
            logger.error(error_msg)
        
        return parsed_doc
    
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from HTML."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            return self._extract_clean_text(soup)
        except Exception as e:
            logger.error(f"Error extracting text from HTML {file_path}: {e}")
            raise
    
    def _extract_enhanced_sections(self, soup) -> List[Dict[str, Any]]:
        """Extract sections from HTML using enhanced scraping methods (pandas + BeautifulSoup)."""
        sections = []
        
        # Find all heading elements (h1, h2, h3, h4, h5, h6)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            try:
                heading_text = heading.get_text(strip=True)
                if not heading_text:
                    continue
                
                # Determine heading level
                level = int(heading.name[1])
                
                # Extract content following this heading using enhanced methods
                content = self._extract_enhanced_section_content(heading)
                
                section = {
                    "heading": heading_text,
                    "level": level,
                    "content": content,
                    "source": "html_enhanced"
                }
                sections.append(section)
                
            except Exception as e:
                logger.warning(f"Error extracting section from HTML: {e}")
        
        # If no headings found, try to extract sections from other structural elements
        if not sections:
            sections = self._extract_structural_sections(soup)
        
        return sections
    
    def _extract_enhanced_section_content(self, heading) -> List[str]:
        """Extract content that follows a heading using enhanced methods including table extraction."""
        content = []
        current = heading.next_sibling
        
        while current:
            if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break  # Stop at next heading
            
            if hasattr(current, 'get_text'):
                # Extract text content
                text = current.get_text(strip=True)
                if text:
                    content.append(text)
                
                # Extract tables using pandas if available
                if current.name == 'table':
                    try:
                        table_content = self._extract_table_content(current)
                        if table_content:
                            content.extend(table_content)
                    except Exception as e:
                        logger.warning(f"Error extracting table: {e}")
            
            current = current.next_sibling
        
        return content
    
    def _extract_table_content(self, table_element) -> List[str]:
        """Extract structured content from HTML tables using pandas."""
        try:
            # Use pandas to read HTML table
            table_html = str(table_element)
            tables = pd.read_html(table_html)
            
            table_content = []
            for i, df in enumerate(tables):
                if not df.empty:
                    # Convert DataFrame to readable text
                    table_text = f"Table {i+1}:\n"
                    table_text += df.to_string(index=False)
                    table_content.append(table_text)
            
            return table_content
        except Exception as e:
            logger.warning(f"Error extracting table with pandas: {e}")
            # Fallback to BeautifulSoup extraction
            return self._extract_table_with_bs4(table_element)
    
    def _extract_table_with_bs4(self, table_element) -> List[str]:
        """Fallback table extraction using BeautifulSoup."""
        table_content = []
        
        # Extract table headers
        headers = []
        for th in table_element.find_all('th'):
            headers.append(th.get_text(strip=True))
        
        if headers:
            table_content.append("Headers: " + " | ".join(headers))
        
        # Extract table rows
        for tr in table_element.find_all('tr'):
            cells = []
            for td in tr.find_all(['td', 'th']):
                cells.append(td.get_text(strip=True))
            if cells:
                table_content.append(" | ".join(cells))
        
        return table_content
    
    def _extract_structural_sections(self, soup) -> List[Dict[str, Any]]:
        """Extract sections from structural HTML elements like div, section, article."""
        sections = []
        
        # Look for common structural elements
        structural_elements = soup.find_all(['div', 'section', 'article', 'main'])
        
        for elem in structural_elements:
            # Check if element has meaningful content
            text = elem.get_text(strip=True)
            if len(text) < 50:  # Skip very short elements
                continue
            
            # Try to find a heading within this element
            heading = elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                heading_text = heading.get_text(strip=True)
                level = int(heading.name[1])
            else:
                # Use element's id, class, or first few words as heading
                heading_text = elem.get('id', elem.get('class', ['Content'])[0] if elem.get('class') else 'Content')
                level = 1
            
            # Extract content
            content = [p.get_text(strip=True) for p in elem.find_all(['p', 'li', 'td']) if p.get_text(strip=True)]
            
            if content:
                section = {
                    "heading": heading_text,
                    "level": level,
                    "content": content,
                    "source": "html_enhanced"
                }
                sections.append(section)
        
        return sections
    
    def _extract_clean_text(self, soup) -> str:
        """Extract clean text from HTML, removing scripts, styles, and navigation."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text

class TextParser(DocumentParser):
    """Plain text document parser."""
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a text file."""
        return (Path(file_path).suffix.lower() == '.txt' and 
                Path(file_path).exists())
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse text document and extract structured content."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        filename = Path(file_path).name
        parsed_doc = ParsedDocument(
            filename=filename,
            file_type="txt",
            sections=[],
            metadata={},
            raw_text="",
            parsing_errors=[]
        )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            parsed_doc.raw_text = content
            
            # Extract title from first line
            lines = content.split('\n')
            if lines:
                first_line = lines[0].strip()
                if first_line.startswith('# '):
                    parsed_doc.title = first_line[2:]  # Remove '# ' prefix
                elif first_line:
                    parsed_doc.title = first_line
            
            # Extract sections based on markdown headers
            sections = []
            current_section = None
            current_content = []
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Check for headers (# ## ###)
                if line.startswith('#'):
                    # Save previous section
                    if current_section:
                        current_section['content'] = current_content
                        sections.append(current_section)
                    
                    # Start new section
                    level = len(line) - len(line.lstrip('#'))
                    title = line.lstrip('#').strip()
                    current_section = {
                        'heading': title,
                        'level': level,
                        'content': [],
                        'page': 1  # Text files don't have pages
                    }
                    current_content = []
                else:
                    # Add to current section content
                    if current_section:
                        current_content.append(line)
                    else:
                        # No section yet, might be title
                        if not parsed_doc.title:
                            parsed_doc.title = line
            
            # Add final section
            if current_section:
                current_section['content'] = current_content
                sections.append(current_section)
            
            parsed_doc.sections = sections
            
        except Exception as e:
            error_msg = f"Error parsing text file {file_path}: {e}"
            parsed_doc.parsing_errors.append(error_msg)
            logger.error(error_msg)
        
        return parsed_doc
    
    def extract_text(self, file_path: str) -> str:
        """Extract raw text from text file."""
        if not self.can_parse(file_path):
            raise ValueError(f"Cannot parse file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise

class DocumentParserFactory:
    """Factory for creating appropriate document parsers."""
    
    def __init__(self):
        """Initialize available parsers."""
        self.parsers = []
        
        if PDF_AVAILABLE:
            self.parsers.append(PDFParser())
        if DOCX_AVAILABLE:
            self.parsers.append(DOCXParser())
        if XML_AVAILABLE:
            self.parsers.append(XMLParser())
        if HTML_AVAILABLE:
            self.parsers.append(HTMLParser())
        
        # Always add text parser
        self.parsers.append(TextParser())
    
    def get_parser(self, file_path: str) -> Optional[DocumentParser]:
        """Get appropriate parser for the given file."""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    def parse_document(self, file_path: str) -> ParsedDocument:
        """Parse document using appropriate parser."""
        parser = self.get_parser(file_path)
        if not parser:
            raise ValueError(f"No parser available for file: {file_path}")
        
        return parser.parse(file_path)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        formats = []
        for parser in self.parsers:
            if isinstance(parser, PDFParser):
                formats.append("PDF")
            elif isinstance(parser, DOCXParser):
                formats.append("DOCX")
            elif isinstance(parser, XMLParser):
                formats.append("XML")
            elif isinstance(parser, HTMLParser):
                formats.append("HTML")
            elif isinstance(parser, TextParser):
                formats.append("TXT")
        return formats

# Convenience function
def parse_document(file_path: str) -> ParsedDocument:
    """Parse a document using the appropriate parser."""
    factory = DocumentParserFactory()
    return factory.parse_document(file_path) 