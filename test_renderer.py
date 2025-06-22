import pytest
import json
from markdown_renderer import render_markdown

# Sample minimal template JSON
SAMPLE_TEMPLATE = {
    "title": "Chapter 1: Overview",
    "sections": [
        {
            "heading": "1.1 Introduction",
            "level": 2,
            "content": [
                "This is a sample paragraph.",
                "• First bullet point",
                "- Second bullet point",
                "Placeholder adjacent {{SpecItem}}text"
            ]
        }
    ]
}

EXPECTED_MARKDOWN = (
    "# Chapter 1: Overview\n"
    "\n"
    "## 1.1 Introduction\n"
    "\n"
    "This is a sample paragraph.\n"
    "\n"
    "* First bullet point\n"
    "\n"
    "* Second bullet point\n"
    "\n"
    "Placeholder adjacent {{SpecItem}} text\n"
    "\n"
)


def test_render_markdown_basic():
    md = render_markdown(SAMPLE_TEMPLATE)
    assert md == EXPECTED_MARKDOWN


def test_empty_section():
    empty_template = {"title": "", "sections": []}
    md = render_markdown(empty_template)
    assert md == ""


def test_no_content_items():
    template = {"title": "Title Only", "sections": [{"heading": "", "level": 1, "content": []} ]}
    md = render_markdown(template)
    assert md.strip() == "# Title Only"
