import json
from typing import Any


def to_json(obj: Any) -> str:
    if hasattr(obj, "to_dict"):
        payload = obj.to_dict()
    elif isinstance(obj, dict):
        payload = obj
    else:
        payload = {"value": obj}
    return json.dumps(payload, indent=2, default=str)
