#!/usr/bin/env python3
"""
Test serialization of pipeline results with enum values.
"""

import json
from enum import Enum

from ai_doc_gen.ui.app import CustomJSONEncoder, serialize_pipeline_results


class TestContentType(Enum):
    SPECIFICATION = "specification"
    PROCEDURE = "procedure"
    WARNING = "warning"

def test_serialization():
    """Test that enum values are properly serialized."""
    print("Testing serialization...")

    # Test data with enum values
    test_data = {
        'content_type': TestContentType.SPECIFICATION,
        'items': [
            {'type': TestContentType.PROCEDURE, 'text': 'test'},
            {'type': TestContentType.WARNING, 'text': 'warning'}
        ],
        'nested': {
            'deep': {
                'enum_value': TestContentType.SPECIFICATION
            }
        }
    }

    # Test our serialization function
    serialized = serialize_pipeline_results(test_data)
    print("Serialized data:")
    print(json.dumps(serialized, indent=2))

    # Test JSON encoder
    encoder = CustomJSONEncoder()
    json_str = encoder.encode(test_data)
    print("\nJSON encoded:")
    print(json_str)

    print("\n✅ Serialization test completed successfully!")

if __name__ == "__main__":
    test_serialization()
