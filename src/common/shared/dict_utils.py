from __future__ import annotations

"""Dictionary utility functions."""

from typing import Any, Dict


def deep_merge(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with overrides taking precedence.
    
    Recursively merges nested dictionaries. Values in overrides take precedence
    over values in defaults.
    
    Args:
        defaults: Base dictionary with default values.
        overrides: Dictionary with override values (takes precedence).
    
    Returns:
        Merged dictionary with defaults and overrides combined.
    """
    result = defaults.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

