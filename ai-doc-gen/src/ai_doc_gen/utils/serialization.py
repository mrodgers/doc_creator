"""
Serialization utilities for AI documentation generation.
"""

import json
from enum import Enum
from typing import Any, Dict, List, Union
from datetime import datetime

class EnhancedJSONEncoder(json.JSONEncoder):
    """Enhanced JSON encoder that handles enums, dates, and other special types."""
    
    def default(self, obj: Any) -> Any:
        """Handle special object types for JSON serialization."""
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'model_dump'):
            # Handle Pydantic models
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            # Handle custom objects with __dict__
            return obj.__dict__
        else:
            return super().default(obj)

def serialize_pipeline_results(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """Serialize pipeline results, handling enums and special types."""
    if isinstance(data, dict):
        return {k: serialize_pipeline_results(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_pipeline_results(item) for item in data]
    elif isinstance(data, Enum):
        return data.value
    elif isinstance(data, datetime):
        return data.isoformat()
    elif hasattr(data, 'model_dump'):
        return data.model_dump()
    else:
        return data

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize an object to JSON string."""
    return json.dumps(obj, cls=EnhancedJSONEncoder, **kwargs)

def safe_json_loads(s: str) -> Any:
    """Safely deserialize a JSON string."""
    return json.loads(s) 