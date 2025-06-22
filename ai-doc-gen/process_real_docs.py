import json

from ai_doc_gen.input_processing import (
    extract_structured_content,
    parse_document,
    validate_document,
)


def to_serializable(obj):
    if hasattr(obj, 'model_dump'):
        d = obj.model_dump()
    elif hasattr(obj, 'dict'):
        d = obj.dict()
    else:
        d = dict(obj)
    # Convert enums to their value
    for k, v in d.items():
        if hasattr(v, 'value'):
            d[k] = v.value
    return d

def process_document(doc_path, output_json):
    print(f"\nProcessing: {doc_path}")
    val = validate_document(doc_path)
    print(f"Validation: {val.is_valid}, Score: {val.score}")
    if not val.is_valid:
        print(f"  Issues: {[i.message for i in val.issues]}")
    parsed = parse_document(doc_path)
    print(f"Parsed: {parsed.filename}, Sections: {len(parsed.sections)}")
    content = extract_structured_content(parsed)
    print(f"Extracted items: {len(content)}")
    with open(output_json, 'w') as f:
        json.dump([to_serializable(c) for c in content], f, indent=2)
    print(f"Saved extracted content to {output_json}")

if __name__ == "__main__":
    process_document("functional_spec.docx", "functional_spec_extracted.json")
    process_document("installation_guide.pdf", "installation_guide_extracted.json")
