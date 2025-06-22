# markdown_renderer.py
"""
Module: Markdown Renderer (Enhanced)

Converts a templated chapter JSON into well-formatted Markdown with:
  - Proper spacing around placeholders
  - Bullet list conversion
  - Blank lines between paragraphs
  - Handling of notes/warnings (future enhancement)

Designed for incremental testing and integration.

Usage:
    from markdown_renderer import render_markdown

    with open('chapter1_template.json') as f:
        template = json.load(f)
    md = render_markdown(template)
    print(md)

Functions:
    - render_markdown(template_json: dict) -> str

Best Practices:
    - Pure function: no side-effects, returns a string
    - Simple, readable code
    - Easily testable via pytest
"""
import json
import re

def render_markdown(template_json: dict) -> str:
    """
    Convert a templated chapter JSON structure into Markdown text.

    Args:
        template_json: Dict with keys 'title' and 'sections'.
            - title: string for top-level title
            - sections: list of sections, each with:
                - heading: section heading text
                - level: integer for Markdown heading level
                - content: list of paragraph/line strings

    Returns:
        A Markdown-formatted string with headings, lists, and paragraphs.
    """
    lines = []
    # Top-level title
    title = template_json.get('title', '').strip()
    if title:
        lines.append(f"# {title}")
        lines.append("")

    # Sections
    for section in template_json.get('sections', []):
        heading = section.get('heading', '').strip()
        level = section.get('level', 1)
        # Cap heading level at 6
        depth = min(max(level, 1), 6)
        if heading:
            lines.append(f"{'#' * depth} {heading}")
            lines.append("")

        # Content paragraphs and lists
        for paragraph in section.get('content', []):
            txt = paragraph.strip()
            if not txt:
                continue

            # Bullet point conversion (from • or -) to markdown list
            if txt.startswith('•') or txt.startswith('-'):
                # Handle both formats: "•text" and "• text"
                if txt.startswith('• '):
                    content = txt[2:].strip()
                else:
                    content = txt[1:].strip()
                txt = f"* {content}"

            # Ensure spacing around placeholders: {{Placeholder}}
            txt = re.sub(r'(?<=\w)(\{\{)', r' \1', txt)
            txt = re.sub(r'(\}\})(?=\w)', r'\1 ', txt)

            lines.append(txt)
            lines.append("")  # Blank line after each paragraph or list item

    # Join all lines into final markdown
    result = "\n".join(lines)
    # Handle empty result case
    if not result.strip():
        return ""
    # Ensure there's exactly two trailing newlines to match expected format
    if result.endswith('\n\n'):
        return result
    elif result.endswith('\n'):
        return result + '\n'
    else:
        return result + '\n\n'

# CLI support
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Render templated JSON to Markdown')
    parser.add_argument('input', help='Path to chapter_template.json')
    parser.add_argument('-o', '--output', help='Output Markdown file', default=None)
    args = parser.parse_args()

    template = json.load(open(args.input))
    md_text = render_markdown(template)
    if args.output:
        with open(args.output, 'w') as outf:
            outf.write(md_text)
        print(f"Markdown written to {args.output}")
    else:
        print(md_text)
