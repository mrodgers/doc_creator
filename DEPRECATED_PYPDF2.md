# ⚠️ DEPRECATED: PyPDF2 Usage

## 🚫 DO NOT USE PyPDF2

**PyPDF2 is deprecated and no longer maintained.** It has been completely removed from this codebase.

## ✅ Use These Alternatives Instead

### Primary: pdfplumber
```python
import pdfplumber

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
```

### Fallback: PyMuPDF (fitz)
```python
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text
```

## 📦 Installation

```bash
# Primary extractor
uv add pdfplumber

# Fallback extractor (optional)
uv add PyMuPDF
```

## 🔍 Why PyPDF2 Was Removed

- **No longer maintained** - Last update was in 2022
- **Security vulnerabilities** - Multiple CVEs reported
- **Poor text extraction** - Inconsistent results
- **Better alternatives** - pdfplumber and PyMuPDF are more reliable

## 🛡️ Safeguards in Place

1. **Clear deprecation notices** in all PDF-related code
2. **Automatic fallback** to pdfplumber → PyMuPDF → placeholder
3. **Comprehensive testing** with alternative extractors
4. **Documentation** clearly states preferred extractors

## 📋 Migration Checklist

- [x] Remove PyPDF2 from dependencies
- [x] Update PDF extractor utility
- [x] Replace PyPDF2 usage in analysis scripts
- [x] Add deprecation warnings
- [x] Update documentation
- [x] Test with alternative extractors

## 🚨 If You See PyPDF2 Usage

1. **Replace immediately** with pdfplumber
2. **Test thoroughly** with your PDF files
3. **Update any dependencies** that might pull in PyPDF2
4. **Add to this checklist** if you find more instances

---

**Remember: PyPDF2 is dead. Use pdfplumber or PyMuPDF instead.** 